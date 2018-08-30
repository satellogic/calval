import os
import glob
import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
import numpy as np
import telluric as tl
from calval.scene_info import SceneInfo
from calval.sat_measurements import band_names
from calval.analysis import toa_irradiance_to_reflectance


logger = logging.getLogger(__name__)


def _stats(img):
    return np.ma.median(img), np.ma.average(img), np.ma.std(img)


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
    def from_path(cls, path):
        sceneinfo = SceneInfo.from_foldername(os.path.basename(path))
        return cls.from_sceneinfo(sceneinfo, path)

    def get_band_path(self, band):
        path = self.sceneinfo.get_band_path(band)
        if '*' in path:
            paths = glob.glob(path)
            assert len(paths) == 1, 'No unique band-path found'
            path = paths[0]
        return path

    def extract_values(self, aoi, bands=band_names, product=None):
        if product is None:
            product = self.sceneinfo.product
        row = OrderedDict()
        for band in bands:
            path = self.get_band_path(band)
            raster = tl.georaster.GeoRaster2.open(path)
            scale = self.get_scale(band, product)
            aoi_raster = raster.crop(aoi).mask(aoi)
            img = aoi_raster.image * scale.multiply + scale.add
            med, avg, std = _stats(img)
            logger.debug('extracted values: med=%s, avg=%s, std=%s', med, avg, std)
            row['{}_median'.format(band)] = med
            row['{}_average'.format(band)] = avg
            row['{}_std'.format(band)] = std
        return row

    def extract_corrected_toa(self, aoi, bands=band_names):
        """
        In landsat, the toa values are not corrected for sun elevation
        This corrects the sun-elevation dependance using the central
        sun angle (for better accuracy use per-pixel sun position).
        """
        toa_row = self.extract_values(aoi, bands, 'toa')
        factor = np.sin(self.sun_average_angle.elevation * np.pi / 180)
        row = OrderedDict()
        for band in bands:
            for stat in ['median', 'average', 'std']:
                prop_name = '{}_{}'.format(band, stat)
                row[prop_name] = toa_row[prop_name] / factor
        return row

    def extract_computed_toa(self, aoi, bands=band_names, corrected=False):
        irradiance_row = self.extract_values(aoi, bands, 'irradiance')
        ignore_sun_zenith = not corrected
        row = OrderedDict()
        for band in bands:
            bandname = self.sceneinfo.band_name(band)
            reflectance_per_unit = toa_irradiance_to_reflectance(
                1.0, self.band_ex_irradiance[bandname], self.center_sunpos, self.timestamp,
                ignore_sun_zenith=ignore_sun_zenith)
            for stat in ['median', 'average', 'std']:
                prop_name = '{}_{}'.format(band, stat)
                row[prop_name] = reflectance_per_unit * irradiance_row[prop_name]
        return row
