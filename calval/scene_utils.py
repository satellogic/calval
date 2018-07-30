import glob
from collections import OrderedDict
import numpy as np
import pandas as pd
import telluric as tl
from calval.sites import get_site_aoi
from calval.sentinel_scenes import SentinelSceneInfo
from calval.landsat_scenes import LandsatSceneInfo
from calval.sat_measurements import SatMeasurements, band_names


_info_classes = [SentinelSceneInfo, LandsatSceneInfo]


def make_sceneinfo(filename):
    for cls in _info_classes:
        scene_info = cls.from_filename(filename)
        if scene_info is not None:
            return scene_info
    raise ValueError('Unknown filename format: {}'.format(filename))


def _stats(img):
    return np.ma.median(img), np.ma.average(img), np.ma.std(img)


def extract_values(info, aoi, bands=band_names):
    row = OrderedDict()
    for band in bands:
        path = info.get_band_path(band)
        if '*' in path:
            paths = glob.glob(path)
            assert len(paths) == 1, 'No unique band-path found'
            path = paths[0]
        raster = tl.georaster.GeoRaster2.open(path)
        scale = info.get_scale(band)
        aoi_raster = raster.crop(aoi).mask(aoi)
        img = aoi_raster.image * scale.multiply + scale.add
        med, avg, std = _stats(img)
        print('--->', band, med, avg, std)
        row['{}_median'.format(band)] = med
        row['{}_average'.format(band)] = avg
        row['{}_std'.format(band)] = std
    return row


def make_sat_measurements(scenes, site_name, product, label=None, bands=['B', 'G', 'R', 'NIR']):
    """
    Given a list of `scenes` (either filenames or SceneInfo objects), filter ther
    ones that match the given `site_name` and `product`, and build SatMeasurements object
    containing the measurement values for the specied `bands`.
    A `label` may be added to tag the resulting SatMeasurements object.
    """
    if len(scenes) and isinstance(scenes[0], str):
        scenes = (make_sceneinfo(scene) for scene in scenes)

    aoi = get_site_aoi(site_name)
    rows = []
    for scene in scenes:
        if not scene.contains_site(site_name):
            continue
        if not scene.product == product:
            continue
        print('archive:', scene.archive_path(), scene.is_archive())
        if not scene.is_scene():
            print('---->extracting scene')
            scene.extract_archive()

        row = OrderedDict(timestamp=scene.timestamp, provider=scene.provider)
        row.update(extract_values(scene, aoi, bands))
        rows.append(row)
    df = pd.DataFrame(rows)
    df = df.set_index('timestamp').sort_index()
    return SatMeasurements(df, site_name, product, label)
