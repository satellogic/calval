import os
import datetime as dt
import pytest
import numpy as np
from testing_utils import normalize_folders_into, config
from calval.normalized_scene import (
    NormalizedSceneId, band_names, NormalizedScene, FilebasedScene, URLScene)

scene_id_strs = [
    'toa_S2B_T49TCF_201806260335',
    'sr_S2B_T49TCF_201806260335',
    'toa_LC08_128032_201805290323'
]
scene_ids = [NormalizedSceneId.from_str(s) for s in scene_id_strs]
scene_id = scene_ids[0]


def test_normalized_scene_id():
    # verify that building adds the default tag
    assert all([str(sid) == s + '_0' for sid, s in zip(scene_ids, scene_id_strs)])
    # verify that tags are considered
    scene_id2 = scene_id.copy_with(tag='1')
    assert scene_id != scene_id2


def test_sceneset_id():
    scene_id2 = scene_id.copy_with(product='blah')
    assert scene_id.sceneset_id == scene_id2.sceneset_id


def test_compare():
    scene_id2 = scene_id.copy_with(timestamp=scene_id.timestamp + dt.timedelta(hours=1))
    assert scene_id < scene_id2


def test_paths():
    "test path-generator methods of the scene_id"
    path, fname = scene_id.metadata_path().rsplit('/', maxsplit=1)
    assert fname.endswith('_metadata.json')
    assert scene_id.product in path and scene_id.satellite in fname
    url_prefix = 'file:///data/scenes/'
    band_urls = scene_id.band_urls(url_prefix)
    assert band_urls['red'] == scene_id.band_url(url_prefix, 'red')
    assert set(band_urls.keys()) == set(band_names)


def test_filebased_scene(module_temp_dir):
    # normalize scene
    normpath = os.path.join(module_temp_dir, 'normalized')
    paths = normalize_folders_into(
        normpath, ['S2A_MSIL1C_20180526T081601_N0206_R121_T36RXU_20180526T120617.SAFE'])
    # load it
    scene = FilebasedScene(paths[0])
    assert scene['productname'] == 'toa'
    assert scene['sceneset_id'] != scene['scene_id']
    assert normpath in scene.band_urls['red']
    # load using metadata filename and urls
    meta_file = scene._metadata_path
    band_urls = dict(scene.band_urls)
    scene2 = FilebasedScene(meta_file, band_urls=band_urls)
    assert scene2.metadata == scene.metadata
    green_tile = scene2.band_tile('green', (2446, 1688, 12))
    assert green_tile.shape == (1, 256, 256)


def test_normalized_scene(module_temp_dir):
    meta = {
        'supplier': 'ESA',
        'satellite_class': 'sentinel2',
        'satellite_name': 'S2A',
        'productname': 'toa',
        'metadata': {},
        'scene_id': 'toa_S2A_T36RXU_201805260819_0',
        'sceneset_id': 'S2A_T36RXU_201805260819',
        'timestamp': '2018-05-26T08:19:19.284000+00:00',
        'last_modified': '2018-10-17T08:03:32.116058+00:00'
    }
    # find the images saved by the filebased test
    sceneid = NormalizedSceneId.from_str(meta['scene_id'])
    norm_dir = os.path.join(module_temp_dir, 'normalized')
    scene_dir = os.path.join(norm_dir, sceneid.scenepath_prefix())
    band_urls = sceneid.band_urls(norm_dir + '/')
    for url in band_urls.values():
        assert url.startswith(scene_dir)
    # verify scene sanity
    normscene = NormalizedScene(meta, band_urls)
    assert str(normscene.scene_info) == normscene['scene_id']
    assert normscene['satellite_class'] == 'sentinel2'
    nir_tile = normscene.band_tile('nir', (2446, 1688, 12))
    assert nir_tile.shape == (1, 256, 256)


@pytest.mark.skipif('azure_blob_prefix' not in config,
                    reason='azure_blob_prefix unconfigured')
def test_url_scene():
    url_prefix = config['azure_blob_prefix']
    scene_id = NormalizedSceneId.from_str('sr_LC08_174039_201805150810_0')
    metadata_path = url_prefix + scene_id.metadata_path()
    scene = URLScene(metadata_path)
    assert scene.scene_info == scene_id
    nir_tile = scene.band_tile('nir', (2446, 1688, 12))
    assert nir_tile.shape == (1, 256, 256)
    scene2 = URLScene(metadata_path, url_prefix + scene_id.dir_path())
    assert scene2.band_urls == scene.band_urls
    # with explicit band_urls:
    scene3 = URLScene(metadata_path, {'green': scene2.band_urls['nir']})
    tile3 = scene3.band_tile('green', (2446, 1688, 12))
    assert np.allclose(tile3.image, nir_tile.image)
