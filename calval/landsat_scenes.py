import os
import datetime as dt
import functools
from collections import namedtuple
import tarfile

from .scene_info import SceneInfo, extract_archive, scaling

_site_prs = {
    'baotou': ['128032', '127032'],
    'negev': ['174039'],
    'rrvalley': ['040033']
}

bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
         'B8', 'B9', 'B10', 'B11', 'BQA']

l2_bands = [
    'sr_band1', 'sr_band2', 'sr_band3', 'sr_band4', 'sr_band5', 'sr_band6', 'sr_band7',
    'sr_aerosol', 'radsat_qa', 'pixel_qa'
]

_band_aliases = dict(
    toa=dict(B='B2', G='B3', R='B4', NIR='B5'),
    sr=dict(B='sr_band2', G='sr_band3', R='sr_band4', NIR='sr_band5'),
)

_scale_values = {'toa': scaling(2e-5, -0.1), 'sr': scaling(1e-4, 0)}

_sceneinfo_flds = [
    ('sat', 4),
    ('pr', 6),
    ('starttime', 8),
    ('num', 2),
    ('category', 2)
]


displayid = namedtuple(
    'displayid',
    ['sat', 'prod', 'pr', 'starttime', 'l1time', 'num', 'category',
     'product', 'scene_id']
)


class LandsatSceneInfo(SceneInfo):
    archive_suffix = '.tar.gz'
    provider = 'landsat8'

    def __init__(self, data, config=None):
        super().__init__(config)
        self._data = data
        self.scene_id = data.scene_id
        self.satellite = data.sat
        self.tile_id = data.pr
        self.timestamp = dt.datetime.strptime(data.starttime, '%Y%m%d')
        self.product = data.product

    @property
    def extract_archive(self):
        extract = functools.partial(
            extract_archive,
            self.archive_path(), self.scene_path(),
            mkdir=True, opener=functools.partial(tarfile.open, mode='r:gz'))
        return extract

    @classmethod
    def from_l2_sceneid(cls, sid):
        flds = sid.split('-')
        if len(flds) != 2:
            return None
        sceneinfo, orderinfo = flds
        if len(sceneinfo) != sum([fldlen for fldname, fldlen in _sceneinfo_flds]):
            return None

        fields = displayid._fields
        data = [None] * len(fields)
        for fldname, fldlen in _sceneinfo_flds:
            fldnum = fields.index(fldname)
            data[fldnum] = sceneinfo[:fldlen]
            sceneinfo = sceneinfo[fldlen:]
        data[fields.index('product')] = 'sr'
        data[fields.index('scene_id')] = sid
        return cls(displayid(*data))

    @classmethod
    def from_filename(cls, fname):
        if not fname.endswith(cls.archive_suffix):
            return None
        sid = fname[:-len(cls.archive_suffix)]
        if '_' not in sid:
            return cls.from_l2_sceneid(sid)

        flds = sid.split('_')
        if len(flds) != 7:
            return None
        flds = flds + ['toa', sid]
        data = displayid(*flds)
        return cls(data)

    def archive_filename(self):
        return self.scene_id + self.archive_suffix

    def scene_filename(self):
        return self.scene_id

    def contains_site(self, site):
        """ TODO calculate using polygons """
        return self.tile_id in _site_prs[site]

    def band_name(self, band):
        return _band_aliases[self.product].get(band, band)

    def get_scale(self, band):
        """ TODO: compute from metadata """
        return _scale_values[self.product]

    def get_band_path(self, band):
        band = self.band_name(band)
        if self.product == 'toa':
            band_fname = '{}_{}.{}'.format(self.scene_id, band, 'TIF')
        else:
            sid = '_'.join([
                part if part is not None else '*'
                for part in self._data[:7]
            ])
            band_fname = '{}_{}.{}'.format(sid, band, 'tif')
        return os.path.join(self.scene_path(), band_fname)
