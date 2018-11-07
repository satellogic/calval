import os
import glob
from mercantile import tiles
import telluric as tl
import calval.config


def _first(x):
    return next(iter(x))


def site_names(shapes_dir=None):
    if shapes_dir is None:
        shapes_dir = calval.config.shapes_dir
    filenames = [os.path.basename(x) for x in glob.glob(os.path.join(shapes_dir, '*_poly.shp'))]
    return [x[:-len('_poly.shp')] for x in filenames]


def get_site_aoi(site_name, shapes_dir=None):
    if shapes_dir is None:
        shapes_dir = calval.config.shapes_dir
    path = os.path.join(shapes_dir, '{}_poly.shp'.format(site_name))
    feature = _first(tl.FileCollection.open(path))
    return feature.geometry


def site_tile(site_name, zoomlevel=13, shapes_dir=None):
    aoi = get_site_aoi(site_name, shapes_dir)
    west, south, east, north = aoi.get_bounds(tl.constants.WGS84_CRS)
    res = list(tiles(west, south, east, north, zoomlevel))
    assert len(res) == 1, "unsupported: target split between tiles"
    return res[0]
