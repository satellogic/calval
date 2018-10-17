import os
import calval.config
from calval.scene_info import SceneInfo
from calval.scene_data import SceneData
# Import provider module to enable the factory mechanism
import calval.sentinel_scenes  # noqa: F401
import calval.landsat_scenes  # noqa: F401

testdir = os.path.abspath(os.path.dirname(__file__))
calval.config.shapes_dir = os.path.join(testdir, 'data', 'sites')
config = dict(SceneInfo.config)
config.update(scenes=os.path.join(testdir, 'data', 'scenes'))


def normalize_folders_into(path, foldernames=None):
    newconfig = dict(config)
    newconfig['normalized'] = path
    srcpath = newconfig['scenes']
    if foldernames is None:
        foldernames = os.listdir(srcpath)
    orig_scenes = [SceneData.from_path(os.path.join(srcpath, x), newconfig)
                   for x in foldernames]
    paths = []
    for scene in orig_scenes:
        paths.append(scene.save_normalized())
    return paths
