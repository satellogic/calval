import os.path
import calval.config
from calval.scene_info import SceneInfo
# Import provider module to enable the factory mechanism
import calval.sentinel_scenes  # noqa: F401
import calval.landsat_scenes  # noqa: F401

testdir = os.path.abspath(os.path.dirname(__file__))
calval.config.shapes_dir = os.path.join(testdir, 'data', 'sites')
config = dict(SceneInfo.config)
config.update(scenes=os.path.join(testdir, 'data', 'scenes'))
