import os
import datetime as dt
from tempfile import TemporaryDirectory
from testing_utils import config
from calval.scene_info import SceneInfo
from calval.scene_data import SceneData
from calval.normalized_scene import NormalizedSceneId, band_names, NormalizedScene

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


def test_normalized_scene():
    with TemporaryDirectory() as folder:
        folder = '/tmp/aaa'
        config2 = dict(config)
        config2['normalized'] = os.path.join(folder, 'normalized')
        # normalize scene
        info = SceneInfo.from_foldername(
            'S2A_MSIL1C_20180526T081601_N0206_R121_T36RXU_20180526T120617.SAFE',
            config=config2)
        s2_scene = SceneData.from_sceneinfo(info)
        path = s2_scene.save_normalized()
        # load it
        normscene = NormalizedScene.from_file(path)
        assert str(normscene.scene_info) == normscene['scene_id']
        assert normscene['satellite_class'] == 'sentinel2'
        green_tile = normscene.band_tile('green', (2446, 1688, 12))
        assert green_tile.shape == (1, 256, 256)
