import os
import pytest
import numpy as np
from testing_utils import config, normalize_folders_into
from calval.providers import SceneInfo
from calval.scene_utils import make_sat_measurements, TilePile
from calval.normalized_scene import band_names
from calval.storage import FileStorage

expected_blue_toa = {'landsat8': 0.21, 'sentinel2': 0.23}
expected_blue_sr = {'landsat8': 0.19}


@pytest.fixture(scope='module')
def norm_scene_storage(module_temp_dir):
    module_temp_dir = '/tmp'
    normpath = os.path.join(module_temp_dir, 'normalized')
    normalize_folders_into(normpath)
    return FileStorage(normpath)


def test_make_sat_measurements():
    foldernames = os.listdir(config['scenes'])
    infos = [SceneInfo.from_foldername(fname, config=config)
             for fname in foldernames]
    sm = make_sat_measurements(infos, 'negev', 'toa')
    for provider in expected_blue_toa.keys():
        rows = sm.df[sm.df['provider'] == provider]
        assert np.allclose(rows[['blue_median', 'blue_average']], expected_blue_toa[provider],
                           atol=0.01)
        std_names = ['{}_std'.format(x) for x in band_names]
        assert np.allclose(rows[std_names], 0, atol=0.05)

    sm_sr = make_sat_measurements(infos, 'negev', 'sr')
    for provider in expected_blue_sr.keys():
        rows = sm_sr.df[sm_sr.df['provider'] == provider]
        assert np.allclose(rows[['blue_median', 'blue_average']], expected_blue_sr[provider],
                           atol=0.01)
        std_names = ['{}_std'.format(x) for x in band_names]
        assert np.allclose(rows[std_names], 0, atol=0.05)


def test_tile_pile(norm_scene_storage):
    scenes = norm_scene_storage.query(product='toa')
    pile = TilePile(scenes, 'green', 'negev', 10)
    assert len(scenes) == pile.raster.image.shape[0]
    assert len(scenes) == len(pile.raster.band_names)
    assert pile.median.band_names == ['green']
    assert np.ma.average(pile.median.image) == pytest.approx(0.2658, rel=1e-3)
    q = pile.quantile_abs_reldiff(pile.median.image, np.arange(0, 1 + 1e-5, 0.25))
    assert q[0] == 0
    q = pile.quantile_reldiff(pile.median.image, np.arange(0, 1 + 1e-5, 0.25))
    assert q[2] == 0
    assert pile.self_abs_reldiff_quantile(0) == 0
    assert pile.self_reldiff_quantile(0.5) == 0
