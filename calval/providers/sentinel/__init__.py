import os
import datetime as dt
import functools
import collections
import zipfile

import numpy as np
from calval.geometry import IncidenceAngle
from calval.normalized_scene import band_names
from calval.satellites.srf import Sentinel2Blue, Sentinel2Green, Sentinel2Red, Sentinel2Nir
from calval.analysis import srf_exatmospheric_irradiance
from calval.providers import SceneInfo, SceneData
from calval.providers.scene_info import extract_archive, scaling
from .sentinel_xml import parse_tile_metadata, parse_xml_metadata

_product_names = {
    'MSIL1C': 'toa',
    'MSIL2A': 'sr'
}

_scale_values = {'toa': scaling(1e-4, 0), 'sr': scaling(1e-4, 0)}

_site_boxes = {
    'baotou': ['T49TCF'],
    'negev': ['T36RXU', 'T36RYU'],
    'rrvalley': ['T11SPC']
}

_band_aliases = dict(
    blue='B02', green='B03', red='B04', nir='B08'
)


# Note: following function does not work for all channels, but correct for the 4 of interest
def _band_id(name):
    "band names (suffix of filenames) is 1-based, whereas id in xml is 0-based"
    return int(name[1:]) - 1


_band_resolutions = dict(
    AOT=10, TCI=10, WVP=10,
    # blue, green, red, nir
    B02=10, B03=10, B04=10, B08=10,
    #
    SCL=20,
    # vegetation (NIR)
    B05=20, B06=20, B07=20, B8A=20,
    # snow/ice/cloud (IR)
    B11=20, B12=20,
    # Aerosol, WV, Cirrus
    B01=60, B09=60, B10=60
)


sentinelid = collections.namedtuple(
    'sentinelid',
    ['mission', 'product', 'captime', 'grid_n', 'grid_r', 'box', 'othertime'])


class SentinelSceneData(SceneData):
    band_ex_irradiance = {
        _band_aliases['blue']: srf_exatmospheric_irradiance(Sentinel2Blue()),
        _band_aliases['green']: srf_exatmospheric_irradiance(Sentinel2Green()),
        _band_aliases['red']: srf_exatmospheric_irradiance(Sentinel2Red()),
        _band_aliases['nir']: srf_exatmospheric_irradiance(Sentinel2Nir())
    }

    def __init__(self, sceneinfo, path=None):
        super().__init__(sceneinfo, path)
        self.granule = self.sceneinfo._get_granule()
        self._read_product_metadata()
        self._read_l1_metadata()

    def _granule_mtd_path(self):
        return os.path.join(self.path, 'GRANULE', self.granule, 'MTD_TL.xml')

    def _product_mtd_path(self):
        return os.path.join(self.path, 'MTD_{}.xml'.format(self.sceneinfo._data.product))

    def _read_product_metadata(self):
        self.product_meta = metadata = parse_xml_metadata(self._product_mtd_path())
        data = metadata['General_Info']['Product_Image_Characteristics']['Reflectance_Conversion']
        self.esuns = [
            data['Solar_Irradiance_List']['SOLAR_IRRADIANCE_{}'.format(
                _band_id(_band_aliases[band]))]
            for band in band_names
        ]
        self.sun_distance = np.sqrt(1.0 / data['U'])  # assuming U is `d(t)` of the TG
        data = metadata['Geometric_Info']['Product_Footprint']['Product_Footprint']
        coords = data['Global_Footprint']['EXT_POS_LIST']
        self.corners = [(coords[i+1], coords[i]) for i in range(0, 8, 2)]
        self.center = tuple(np.average(self.corners, axis=0))
        self.cloud_coverage = metadata['Quality_Indicators_Info']['Cloud_Coverage_Assessment']

    def _read_l1_metadata(self):
        self.metadata = metadata = parse_tile_metadata(self._granule_mtd_path())
        self.timestamp = metadata['General_Info']['SENSING_TIME']

        def _view_angle(bandid):
            mean_view_list = metadata['Geometric_Info']['Tile_Angles']['Mean_Viewing_Incidence_Angle_List']
            return mean_view_list['Mean_Viewing_Incidence_Angle_{}'.format(bandid)]
        assert _view_angle(_band_id(_band_aliases['green']))['AZIMUTH_ANGLE_unit'] == 'deg'
        # NOTE: Seem to be large differences between viewing angles of the channels
        # TODO: make per-channel calcs!
        angles = [_view_angle(_band_id(_band_aliases[band]))['AZIMUTH_ANGLE']
                  for band in band_names]
        view_average_azimuth = np.average(angles)
        angles = [_view_angle(_band_id(_band_aliases[band]))['ZENITH_ANGLE']
                  for band in band_names]
        view_average_zenith = np.average(angles)
        self.sat_average_angle = IncidenceAngle(view_average_azimuth, 90 - view_average_zenith)
        sun_azimuth = metadata['Geometric_Info']['Tile_Angles']['Mean_Sun_Angle']['AZIMUTH_ANGLE']
        sun_zenith = metadata['Geometric_Info']['Tile_Angles']['Mean_Sun_Angle']['ZENITH_ANGLE']
        self.sun_average_angle = IncidenceAngle(sun_azimuth, 90 - sun_zenith)

    def get_metadata(self):
        meta = {
            'center': self.center,
            'esuns': self.esuns,
            'sun_distance': self.sun_distance,  # based on `U` from metadata
            'sat_average_angle': self.sat_average_angle.to_dict(),
            'sun_average_angle': self.sun_average_angle.to_dict(),
            'cloud_cover': self.cloud_coverage
        }
        return meta

    def get_scale(self, band, product):
        """ TODO: compute from metadata """
        return _scale_values[product]


class SentinelSceneInfo(SceneInfo):
    archive_suffix = '.zip'
    folder_suffix = '.SAFE'
    provider = 'sentinel2'

    date_fmt = '%Y%m%dT%H%M%S'
    scenedata_class = SentinelSceneData

    def __init__(self, data, config=None):
        super().__init__(config)
        self._data = data
        self.scene_id = '_'.join(data)
        self.satellite = data.mission
        self.tile_id = data.box
        self.timestamp = dt.datetime.strptime(data.captime, self.date_fmt)
        self.product = _product_names[data.product]
        self.products = [self.product]

    @property
    def extract_archive(self):
        extract = functools.partial(
            extract_archive,
            self.archive_path(), self.scene_path(),
            mkdir=False, opener=zipfile.ZipFile)
        return extract

    @classmethod
    def from_foldername(cls, fname, config):
        if not fname.endswith(cls.folder_suffix):
            return None
        sid = fname[:-len(cls.folder_suffix)]
        if len(sid.split('_')) != 7:
            return None
        data = sentinelid(*sid.split('_'))
        return cls(data, config)

    @classmethod
    def from_filename(cls, fname, config):
        if not fname.endswith(cls.archive_suffix):
            return None
        sid = fname[:-len(cls.archive_suffix)]
        if len(sid.split('_')) != 7:
            return None
        data = sentinelid(*sid.split('_'))
        return cls(data, config)

    def archive_filename(self):
        return self.scene_id + self.archive_suffix

    def scene_filename(self):
        return self.scene_id + '.SAFE'

    def contains_site(self, site):
        """ TODO calculate using polygons """
        return self.tile_id in _site_boxes[site]

    def band_name(self, band):
        return _band_aliases.get(band, band)

    def _get_granule(self):
        path = os.path.join(self.scene_path(), 'GRANULE')
        granules = os.listdir(path)
        assert len(granules) == 1
        return granules[0]

    def get_band_path(self, band):
        band = self.band_name(band)
        granule = self._get_granule()
        path = os.path.join(self.scene_path(), 'GRANULE', granule, 'IMG_DATA')
        if self.product == 'sr':
            res = '{}m'.format(_band_resolutions[band])
            path = os.path.join(path, 'R' + res)
            band_fnames = os.listdir(path)
            band_fname = '{}_{}_{}_{}.jp2'.format(
                self.tile_id, self.timestamp.strftime(self.date_fmt),
                band, res)
            assert band_fname in band_fnames
        else:
            band_fname = '{}_{}_{}.jp2'.format(
                self.tile_id, self.timestamp.strftime(self.date_fmt), band)
        path = os.path.join(path, band_fname)
        return path
