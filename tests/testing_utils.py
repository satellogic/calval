"""
Configuration of testing environment,
and utils to be used in test functions.
"""
import os
import warnings
import calval.config
from calval.providers import SceneInfo, SceneData
from calval.azure_storage import AzureStorage
# Import provider modules to enable the factory mechanism
import calval.providers.sentinel  # noqa: F401
import calval.providers.landsat  # noqa: F401

testdir = os.path.abspath(os.path.dirname(__file__))
original_shapes_dir = calval.config.shapes_dir
calval.config.shapes_dir = os.path.join(testdir, 'data', 'sites')
config = dict(SceneInfo.config)
config.update(scenes=os.path.join(testdir, 'data', 'scenes'))

# Following extra settings do not appear in normal config: maybe add there:
# if azure is configured, setup url prefix
cstring = os.environ.get('AZURE_CICD_CONNECTION')
if cstring is not None:
    storage = AzureStorage(cstring, 'cicd', 'calval_test/')
    config.update(
        azure_cicd_connection=cstring,
        azure_blob_prefix=storage.public_url_prefix())
else:
    warnings.warn('azure_blob_prefix not configured - some tests will be skipped')

# Following env setting is requied for `get_tile` to work over https
# (rasterio / libcurl issue)
os.environ['CURL_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'


def normalize_folders_into(path, foldernames=None):
    """
    Read provider scenes from configured scenes dir and normalize them into
    the specified path.
    If `foldernames` not specified, all scenes will be normalized
    """
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
