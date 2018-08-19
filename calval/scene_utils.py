from collections import OrderedDict
import pandas as pd
from calval.sites import get_site_aoi
from calval.sat_measurements import SatMeasurements
from calval.scene_info import SceneInfo
from calval.scene_data import SceneData
# Import provider module to enable the factory mechanism
import calval.sentinel_scenes  # noqa: F401
import calval.landsat_scenes  # noqa: F401


def make_sat_measurements(scenes, site_name, product, label=None, bands=['B', 'G', 'R', 'NIR']):
    """
    Given a list of `scenes` (either filenames or SceneInfo objects), filter ther
    ones that match the given `site_name` and `product`, and build SatMeasurements object
    containing the measurement values for the specied `bands`.
    A `label` may be added to tag the resulting SatMeasurements object.
    """
    if len(scenes) and isinstance(scenes[0], str):
        scenes = (SceneInfo.from_filename(scene) for scene in scenes)

    aoi = get_site_aoi(site_name)
    rows = []
    for sceneinfo in scenes:
        if not sceneinfo.contains_site(site_name):
            continue
        if not sceneinfo.product == product:
            continue
        print('archive:', sceneinfo.archive_path(), sceneinfo.is_archive())
        if not sceneinfo.is_scene():
            print('---->extracting sceneinfo')
            sceneinfo.extract_archive()
        scenedata = SceneData.from_sceneinfo(sceneinfo)
        # reading the metadata provides better timestamp than the sceneinfo one
        scenedata._read_l1_metadata()

        row = OrderedDict(timestamp=scenedata.timestamp, provider=sceneinfo.provider)
        row.update(scenedata.extract_values(aoi, bands))
        rows.append(row)
    df = pd.DataFrame(rows)
    df = df.set_index('timestamp').sort_index()
    return SatMeasurements(df, site_name, product, label)
