import os
import datetime as dt
import functools
import collections
import zipfile

from .scene_info import SceneInfo, extract_archive, scaling

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
    B='B02', G='B03', R='B04', NIR='B08'
)

_band_resolutions = dict(
    AOT=10, TCI=10, WVP=10,
    # B, G, R, NIR
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


class SentinelSceneInfo(SceneInfo):
    archive_suffix = '.zip'
    provider = 'sentinel2'

    date_fmt = '%Y%m%dT%H%M%S'

    def __init__(self, data, config=None):
        super().__init__(config)
        self._data = data
        self.scene_id = '_'.join(data)
        self.satellite = data.mission
        self.tile_id = data.box
        self.timestamp = dt.datetime.strptime(data.captime, self.date_fmt)
        self.product = _product_names[data.product]

    @property
    def extract_archive(self):
        extract = functools.partial(
            extract_archive,
            self.archive_path(), self.scene_path(),
            mkdir=False, opener=zipfile.ZipFile)
        return extract

    @classmethod
    def from_filename(cls, fname):
        if not fname.endswith(cls.archive_suffix):
            return None
        sid = fname[:-len(cls.archive_suffix)]
        if len(sid.split('_')) != 7:
            return None
        data = sentinelid(*sid.split('_'))
        return cls(data)

    def archive_filename(self):
        return self.scene_id + self.archive_suffix

    def scene_filename(self):
        return self.scene_id + '.SAFE'

    def contains_site(self, site):
        """ TODO calculate using polygons """
        return self.tile_id in _site_boxes[site]

    def band_name(self, band):
        return _band_aliases.get(band, band)

    def get_scale(self, band):
        """ TODO: compute from metadata """
        return _scale_values[self.product]

    def get_band_path(self, band):
        band = self.band_name(band)
        path = os.path.join(self.scene_path(), 'GRANULE')
        granules = os.listdir(path)
        assert len(granules) == 1
        granule = granules[0]
        path = os.path.join(path, granule, 'IMG_DATA')
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
