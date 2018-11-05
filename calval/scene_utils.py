import logging
from collections import OrderedDict
import numpy as np
import pandas as pd
from calval.utils import cached_property, nanquantile
from calval.raster_utils import uncached_get_tile
from calval.sites import get_site_aoi, site_tile
from calval.sat_measurements import SatMeasurements
from calval.normalized_scene import band_names
from calval.providers import SceneInfo, SceneData
# Import provider module to enable the factory mechanism
import calval.providers.sentinel  # noqa: F401
import calval.providers.landsat  # noqa: F401


logger = logging.getLogger(__name__)


class TilePile:
    """
    pixel-by-pixel comparison of several scenes by extraction of common tile
    Can compute the median tile (a numpy maskedarray, with the median of each pixel)
    and statistics of relative distances from a reference tile.
    """
    def __init__(self, scenes, band, site_name, base_zoomlevel=13, zoomlevel=None, get_tile=uncached_get_tile):
        """
        Extract a common tile (bounds determined by coords of the site `site_name`,
        and `base_zoomlevel`, resolution specified by `zoomlevel`)
        """
        self.band = band
        self.scenes = scenes
        self.tile_coords = site_tile(site_name, base_zoomlevel)
        if zoomlevel is None:
            zoomlevel = base_zoomlevel
        self.zoomlevel = zoomlevel
        tiles = [
            scene.band_tile(band, self.tile_coords, zoomlevel=zoomlevel, get_tile=get_tile)
            for scene in scenes
        ]
        alltiles = np.ma.concatenate([x.image for x in tiles], axis=0)
        self.raster = tiles[0].copy_with(
            image=alltiles, band_names=[str(scene.scene_info) for scene in scenes])

    @cached_property
    def median(self):
        median = np.ma.median(self.raster.image, axis=0)
        return self.raster.copy_with(image=median, band_names=[self.band])

    def quantile_abs_reldiff(self, ref_band, q):
        """
        quantile `q` of abs(rel distance) from `ref_band` (masked array)
        """
        absdiff = np.ma.abs(self.raster.image - ref_band) / ref_band
        return nanquantile(absdiff.filled(np.nan), q)

    def quantile_reldiff(self, ref_band, q):
        """quantile `q` of relative distance from `ref_band` (masked array)"""
        diff = (self.raster.image - ref_band) / ref_band
        return nanquantile(diff.filled(np.nan), q)

    # TODO: for small number of rasters (in particular 2 & 3), need self-distance from median.
    # correct way is to do weighted quantile, giving weight=0.5 for two mid-values if even, and
    # weight=0 for the mid-value if odd. This requires sorting etc.
    def self_abs_reldiff_quantile(self, q):
        return self.quantile_abs_reldiff(self.median.image, q)

    def self_reldiff_quantile(self, q):
        return self.quantile_reldiff(self.median.image, q)


def make_sat_measurements(scenes, site_name, product, label=None, bands=band_names, provider=None,
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
        # reading the metadata provides better timestamp than the sceneinfo one,
        # and also makes available the proper scaling factors (execute by default?)
        scenedata = SceneData.from_sceneinfo(sceneinfo)
        row = OrderedDict(timestamp=scenedata.timestamp, provider=sceneinfo.provider)
        logger.debug('extracting %s for bands %s', product, bands)
        if product.startswith('computed_toa'):
            row.update(scenedata.extract_computed_toa(aoi, bands, compute_correction))
        else:
            if ((not correct_landsat_toa) and sceneinfo.provider == 'landsat8' and product == 'toa'):
                row.update(scenedata.extract_values(aoi, bands, product='toa_raw'))
            else:
                row.update(scenedata.extract_values(aoi, bands, product=product))
        rows.append(row)
    df = pd.DataFrame(rows)
    df = df.set_index('timestamp').sort_index()
    return SatMeasurements(df, site_name, product, label)
