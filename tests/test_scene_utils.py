import os
import numpy as np
import calval.config
from calval.scene_info import SceneInfo
from calval.scene_utils import make_sat_measurements
from calval.sat_measurements import band_names
# Import provider module to enable the factory mechanism
import calval.sentinel_scenes  # noqa: F401
import calval.landsat_scenes  # noqa: F401

testdir = os.path.abspath(os.path.dirname(__file__))
calval.config.shapes_dir = os.path.join(testdir, 'data', 'sites')
config = dict(SceneInfo.config)
config.update(scenes=os.path.join(testdir, 'data', 'scenes'))

expected_blue_toa = {'landsat8': 0.21, 'sentinel2': 0.23}
expected_blue_sr = {'landsat8': 0.19}


def test_make_sat_measurements():
    foldernames = os.listdir(config['scenes'])
    infos = [SceneInfo.from_foldername(fname, config=config)
             for fname in foldernames]
    sm = make_sat_measurements(infos, 'negev', 'toa')
    for provider in expected_blue_toa.keys():
        rows = sm.df[sm.df['provider'] == provider]
        assert np.allclose(rows[['B_median', 'B_average']], expected_blue_toa[provider],
                           atol=0.01)
        std_names = ['{}_std'.format(x) for x in band_names]
        assert np.allclose(rows[std_names], 0, atol=0.05)

    sm_sr = make_sat_measurements(infos, 'negev', 'sr')
    for provider in expected_blue_sr.keys():
        rows = sm_sr.df[sm_sr.df['provider'] == provider]
        assert np.allclose(rows[['B_median', 'B_average']], expected_blue_sr[provider],
                           atol=0.01)
        std_names = ['{}_std'.format(x) for x in band_names]
        assert np.allclose(rows[std_names], 0, atol=0.05)
