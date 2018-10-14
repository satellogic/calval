import os
import numpy as np
from testing_utils import config
from calval.scene_info import SceneInfo
from calval.scene_utils import make_sat_measurements
from calval.sat_measurements import band_names

expected_blue_toa = {'landsat8': 0.21, 'sentinel2': 0.23}
expected_blue_sr = {'landsat8': 0.19}


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
