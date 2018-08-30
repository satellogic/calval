import logging
from collections import OrderedDict
import pandas as pd
from calval.sites import get_site_aoi
from calval.sat_measurements import SatMeasurements
from calval.scene_info import SceneInfo
from calval.scene_data import SceneData
# Import provider module to enable the factory mechanism
import calval.sentinel_scenes  # noqa: F401
import calval.landsat_scenes  # noqa: F401


logger = logging.getLogger(__name__)


def make_sat_measurements(scenes, site_name, product, label=None, bands=['B', 'G', 'R', 'NIR'], provider=None,
                          correct_landsat_toa=False):
    """
    Given a list of `scenes` (either filenames or SceneInfo objects), filter ther
    ones that match the given `site_name` and `product`, and build SatMeasurements object
    containing the measurement values for the specied `bands`.
    A `label` may be added to tag the resulting SatMeasurements object.
    In `provider` is specifed, we filter only products of that provider.
    """
    if len(scenes) and isinstance(scenes[0], str):
        scenes = (SceneInfo.from_filename(scene) for scene in scenes)

    aoi = get_site_aoi(site_name)
    if product.startswith('computed_toa'):
        req_product = 'irradiance'
        compute_correction = product.endswith('_corrected')
    else:
        req_product = product
        compute_correction = None
    rows = []
    for sceneinfo in scenes:
        if not sceneinfo.contains_site(site_name):
            continue
        if req_product not in sceneinfo.products:
            continue
        if provider is not None and sceneinfo.provider != provider:
            continue
        logger.debug('archive: %s exists?: %s', sceneinfo.archive_path(), sceneinfo.is_archive())
        if not sceneinfo.is_scene():
            logger.info('archive: %s: extracting scene from archive', sceneinfo.archive_path())
            sceneinfo.extract_archive()
        scenedata = SceneData.from_sceneinfo(sceneinfo)
        # reading the metadata provides better timestamp than the sceneinfo one,
        # and also makes available the proper scaling factors (execute by default?)
        scenedata._read_l1_metadata()

        row = OrderedDict(timestamp=scenedata.timestamp, provider=sceneinfo.provider)
        logger.debug('extracting %s for bands %s', product, bands)
        if product.startswith('computed_toa'):
            row.update(scenedata.extract_computed_toa(aoi, bands, compute_correction))
        else:
            # TODO: move this if into LandsatSceneData.extract_values
            if (correct_landsat_toa and sceneinfo.provider == 'landsat8' and product == 'toa'):
                row.update(scenedata.extract_corrected_toa(aoi, bands))
            else:
                row.update(scenedata.extract_values(aoi, bands, product=product))
        rows.append(row)
    df = pd.DataFrame(rows)
    df = df.set_index('timestamp').sort_index()
    return SatMeasurements(df, site_name, product, label)
