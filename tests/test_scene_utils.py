import os
from calval.scene_info import SceneInfo
from calval.scene_utils import make_sat_measurements
# Import provider module to enable the factory mechanism
import calval.sentinel_scenes  # noqa: F401
import calval.landsat_scenes  # noqa: F401

testdir = os.path.abspath(os.path.dirname(__file__))
config = dict(SceneInfo.config)
config.update(scenes=os.path.join(testdir, 'data', 'scenes'))


def test_make_sat_measurements():
    foldernames = os.listdir(config['scenes'])
    infos = [SceneInfo.from_foldername(fname, config=config)
             for fname in foldernames]
    sm = make_sat_measurements(infos, 'negev', 'toa')
    print(sm.df)
    sm_sr = make_sat_measurements(infos, 'negev', 'sr')
    print('--->sr')
    print(sm_sr.df)
