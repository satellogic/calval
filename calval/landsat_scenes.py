import os
import glob
import datetime as dt
import functools
from collections import namedtuple
import tarfile

import dateutil.parser
import numpy as np
from calval.geometry import IncidenceAngle
from calval.scene_info import SceneInfo, extract_archive, scaling
from calval.scene_data import SceneData
from calval.landsat_mtl import read_mtl
from calval.sun_position import SunPosition

_site_prs = {
    'baotou': ['128032', '127032'],
    'negev': ['174039'],
    'rrvalley': ['040033']
}

bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
         'B8', 'B9', 'B10', 'B11', 'BQA']

band_index = {'B{}'.format(i+1): i for i in range(11)}

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


def _displayid_str(displayid):
    return '_'.join(fld or '*' for fld in displayid[:7])


class LandsatSceneData(SceneData):
    def __init__(self, sceneinfo, path=None):
        super().__init__(sceneinfo, path)
        self._set_l1_sceneinfo()
        if 'toa' in self.products:
            self.products.append('irradiance')

    def _set_l1_sceneinfo(self):
        paths = glob.glob(os.path.join(self.path, self.sceneinfo.l1_mtl_filename()))
        assert len(paths) == 1, 'No unique MTL file found'
        l1_id = os.path.basename(paths[0])[:-len('_MTL.txt')]
        self.l1_sceneinfo = SceneInfo.from_foldername(l1_id)

    def _mtl_path(self):
        return os.path.join(self.path, self.l1_sceneinfo.l1_mtl_filename())

    def _read_l1_metadata(self):
        self.l1_metadata = meta = read_mtl(self._mtl_path())['L1_METADATA_FILE']

        data = meta['PRODUCT_METADATA']
        timestamp = dateutil.parser.parse(
            data['DATE_ACQUIRED'].strftime('%Y-%m-%d') + 'T' + data['SCENE_CENTER_TIME'])
        self.timestamp = timestamp
        self.corners = [(data['CORNER_{}_LON_PRODUCT'.format(x)], data['CORNER_{}_LAT_PRODUCT'.format(x)])
                        for x in ['UL', 'UR', 'LR', 'LL']]
        self.center = tuple(np.average(self.corners, axis=0))
        self.center_sunpos = SunPosition(self.center[0], self.center[1], 0)

        data = meta['RADIOMETRIC_RESCALING']
        scalings = []
        for iband in range(9):
            scalings.append(scaling(
                data['REFLECTANCE_MULT_BAND_{}'.format(iband+1)],
                data['REFLECTANCE_ADD_BAND_{}'.format(iband+1)]))
        rad_scalings = []
        for iband in range(11):
            rad_scalings.append(scaling(
                data['RADIANCE_MULT_BAND_{}'.format(iband+1)],
                data['RADIANCE_ADD_BAND_{}'.format(iband+1)]))
        self.l1_scalings = scalings, rad_scalings

        data = meta['IMAGE_ATTRIBUTES']
        for attr in ['roll_angle', 'earth_sun_distance', 'cloud_cover', 'cloud_cover_land']:
            setattr(self, attr, data[attr.upper()])
        self.sun_average_angle = IncidenceAngle(data['SUN_AZIMUTH'], data['SUN_ELEVATION'])
        self.sun_distance = data['EARTH_SUN_DISTANCE']
        # The view zenith is assumed to be 0 in landsat's own computation (so azimuth does not matter)
        # For accurate computation, need the Azimuth and the Roll
        # * "Positive roll is to the port side of the spacecraft and the negative roll is to the starboard side"
        #   i.e. it's relative to spacecraft's orientation - need Azimuth...
        # * Azimuth can be computed from image corners
        #   https://gis.stackexchange.com/questions/98425/calculate-actual-landsat-image-corner-coordinates-to-derive-azimuth-heading?rq=1
        self.sat_average_angle = IncidenceAngle(180, 90)

    def get_scale(self, band, product):
        if product not in self.products:
            raise ValueError('not available')
        if product == 'sr':
            return _scale_values['sr']

        assert hasattr(self, 'l1_scalings')
        band_ind = band_index[self.sceneinfo.band_name(band)]
        scaling = self.l1_scalings[{'toa': 0, 'irradiance': 1}[product]][band_ind]
        if product == 'toa':
            assert scaling == _scale_values['toa']
        return scaling


class LandsatSceneInfo(SceneInfo):
    archive_suffix = '.tar.gz'
    provider = 'landsat8'
    scenedata_class = LandsatSceneData

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
    def from_foldername(cls, fname):
        if not fname.startswith('LC08'):
            return None
        if '_' not in fname:
            return cls.from_l2_sceneid(fname)
        flds = fname.split('_')
        if len(flds) != 7:
            return None
        flds = flds + ['toa', fname]
        data = displayid(*flds)
        return cls(data)

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

    def l1_mtl_filename(self):
        return _displayid_str(self._data) + '_MTL.txt'
