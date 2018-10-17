import os
import glob
import logging
import json
from abc import ABC, abstractmethod
from collections import OrderedDict
import datetime as dt
import numpy as np
import rasterio as rio
import telluric as tl
from calval.normalized_scene import band_names, NormalizedSceneId
from calval.analysis import toa_irradiance_to_reflectance
from .scene_info import SceneInfo


logger = logging.getLogger(__name__)


def _stats(img):
    return np.ma.median(img), np.ma.average(img), np.ma.std(img)


def set_zero_nodata(raster):
    """
    Mask out any pixels which have value=0 (in addition to previously masked pixels)
    """
    return raster.copy_with(image=raster.image.filled(0), nodata=0)


def save_with_nodata(raster, path, resampling=rio.enums.Resampling.cubic):
    size = raster.image.shape
    params = {
        'mode': 'w',
        'transform': raster.affine, 'crs': raster.crs,
        'driver': 'GTiff',
        'width': size[2], 'height': size[1], 'count': size[0],
        'dtype': rio.uint16,
        'nodata': 0,
        'blockxsize': min(256, size[2]), 'blockysize': min(256, size[1]),
        'tiled': True,
        'compress': rio.enums.Compression.lzw.name
    }
    img = raster.image.filled(0)
    with raster._raster_opener(path, **params) as r:
        for band in range(size[0]):
            r.write_band(1 + band, img[band, :, :])

        tags_to_save = {'telluric_band_names': json.dumps(raster.band_names)}
        r.update_tags(**tags_to_save)

        factors = raster._overviews_factors(256)
        r.build_overviews(factors, resampling=resampling)
        r.update_tags(ns='rio_overview', resampling=resampling.name)


class SceneData(ABC):
    """
    Base class for provider-specific scene data, represented as an unpacked directory,
    with metadata and image files.
    """
    @abstractmethod
    def __init__(self, sceneinfo, path=None):
        assert sceneinfo.scenedata_class == self.__class__, 'Invalid direct constructor call'
        if path is None:
            path = sceneinfo.scene_path()
        assert os.path.isdir(path)
        self.sceneinfo = sceneinfo
        self.path = path

    @classmethod
    def from_sceneinfo(cls, sceneinfo, path=None):
        assert issubclass(sceneinfo.scenedata_class, cls), 'Bad SceneInfo'
        return sceneinfo.scenedata_class(sceneinfo, path)

    @classmethod
    def from_path(cls, path, config=None):
        sceneinfo = SceneInfo.from_foldername(os.path.basename(path), config=config)
        return cls.from_sceneinfo(sceneinfo, path)

    def get_band_path(self, band):
        path = self.sceneinfo.get_band_path(band)
        if '*' in path:
            paths = glob.glob(path)
            assert len(paths) == 1, 'No unique band-path found'
            path = paths[0]
        return path

    def raster(self, band, aoi=None):
        """
        get the raster for relevant band
        `aoi` may be specified to avoid reading the whole raster
        """
        path = self.get_band_path(band)
        raster = tl.georaster.GeoRaster2.open(path)
        if aoi is not None:
            raster = raster.crop(aoi)
        # both L8 and S2 use nodata=0, but do not mark it in the metadata, so telluric does not
        # load them properly. Fix that explicitly (mainly for landsat, as sentinel images do not
        # normally contain nodata pixels).
        raster = set_zero_nodata(raster)
        if aoi is not None:
            raster = raster.mask(aoi)
        return raster

    # Note: for landsat, we override this to provide corrected toa as well as toa_raw
    def scale_image(self, image, band, product=None):
        """
        scale the image according to the appropriate scaling factor
        from the metadata
        """
        if product is None:
            product = self.sceneinfo.product
        scale = self.get_scale(band, product)
        float_image = image * scale.multiply + scale.add
        return float_image

    def float_image(self, band, product=None, aoi=None):
        raster = self.raster(band, aoi)
        return self.scale_image(raster.image, band, product)

    def normalized_raster(self, band, product=None):
        maxword = 1 << 16
        raster = self.raster(band)
        float_img = self.scale_image(raster.image, band, product)
        # encode to 16 bits
        # Note: exatmospheric solar irradiance for blue is around 2 W/(m^2 nm),
        #    so reflected lambertian irrad can be upto 2/pi ~ 0.640 W/(m^2 nm sr)
        #    hence, clipping to [0:1] should be OK
        img = np.ma.round(float_img * maxword)
        img = np.ma.clip(img, 1, maxword - 1).astype(np.uint16)
        raster = raster.copy_with(image=img)
        return raster

    def extract_values(self, aoi, bands=band_names, product=None):
        row = OrderedDict()
        for band in bands:
            img = self.float_image(band, product, aoi)
            med, avg, std = _stats(img)
            logger.debug('extracted values: med=%s, avg=%s, std=%s', med, avg, std)
            row['{}_median'.format(band)] = med
            row['{}_average'.format(band)] = avg
            row['{}_std'.format(band)] = std
        return row

    def extract_computed_toa(self, aoi, bands=band_names, corrected=False):
        irradiance_row = self.extract_values(aoi, bands, 'irradiance')
        ignore_sun_zenith = not corrected
        row = OrderedDict()
        for band in bands:
            bandname = self.sceneinfo.band_name(band)
            reflectance_per_unit = toa_irradiance_to_reflectance(
                1.0, self.band_ex_irradiance[bandname],
                self.center_sunpos, self.timestamp, ignore_sun_zenith=ignore_sun_zenith)
            for stat in ['median', 'average', 'std']:
                prop_name = '{}_{}'.format(band, stat)
                row[prop_name] = reflectance_per_unit * irradiance_row[prop_name]
        return row

    def json_params(self, product=None):
        if product is None:
            product = self.sceneinfo.product

        footprint = self.raster('green').footprint().get_shape(tl.constants.WGS84_CRS)
        footprint_dict = {
            'coordinates': [list(footprint.boundary.coords)],
            'type': footprint.type
        }
        sceneid = NormalizedSceneId.from_str(self.sceneinfo.fname_prefix(product, self.timestamp))
        metadata = self.get_metadata()

        params = {
            'supplier': {'landsat8': 'NASA', 'sentinel2': 'ESA'}[self.sceneinfo.provider],
            'satellite_class': self.sceneinfo.provider,
            'satellite_name': self.sceneinfo.satellite,
            'productname': product,
            'footprint': footprint_dict,
            'metadata': metadata,
            'scene_id': str(sceneid),
            'sceneset_id': str(sceneid.sceneset_id),
            'timestamp': self.timestamp.replace(
                tzinfo=dt.timezone.utc).isoformat()  # self.timestamp is unaware
            # 'last_modified': '',
            # 'attachments': [],
            # 'rasters': [], # {'bands': [bandname], 'filename':, 'scene':, ...}
            # 'bands': {},  # bandname: [rasternum]
        }
        return params

    def _normalized_dirname(self, product=None):
        dirname = os.path.join(
            self.sceneinfo._data_path('normalized'),
            self.sceneinfo.blob_prefix(product, self.timestamp))
        return dirname

    def get_normalized_path(self, band, product=None):
        dirname = self._normalized_dirname(product)
        scene_id = self.sceneinfo.fname_prefix(product, self.timestamp)
        return os.path.join(dirname, '{}_{}.tif'.format(scene_id, band))

    def get_metadata_path(self, product=None):
        dirname = self._normalized_dirname(product)
        scene_id = self.sceneinfo.fname_prefix(product, self.timestamp)
        return os.path.join(dirname, '{}_metadata.json'.format(scene_id))

    def save_normalized(self, bands=band_names, product=None):
        dirname = self._normalized_dirname(product)
        os.makedirs(dirname, exist_ok=True)
        params = self.json_params(product=product)
        scene_id = params['scene_id']
        for band in bands:
            fname = '{}_{}.tif'.format(scene_id, band)
            path = os.path.join(dirname, fname)
            raster = self.normalized_raster(band, product)
            save_with_nodata(raster, path, resampling=rio.enums.Resampling.gauss)
            # TODO: add raster to params?

        params['last_modified'] = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()
        path = os.path.join(dirname, '{}_metadata.json'.format(scene_id))
        with open(path, 'w') as f:
            json.dump(params, f, indent=4)
        return path
