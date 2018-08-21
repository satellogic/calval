import os
import glob
from abc import ABC, abstractmethod
from collections import OrderedDict
import numpy as np
import telluric as tl
from calval.scene_info import SceneInfo
from calval.sat_measurements import band_names


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

    def extract_values(self, aoi, bands=band_names):
        row = OrderedDict()
        for band in bands:
            path = self.get_band_path(band)
            raster = tl.georaster.GeoRaster2.open(path)
            scale = self.sceneinfo.get_scale(band)
            aoi_raster = raster.crop(aoi).mask(aoi)
            img = aoi_raster.image * scale.multiply + scale.add
            med, avg, std = _stats(img)
            print('--->', band, med, avg, std)
            row['{}_median'.format(band)] = med
            row['{}_average'.format(band)] = avg
            row['{}_std'.format(band)] = std
        return row
