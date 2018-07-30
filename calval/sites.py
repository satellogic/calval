import os
import telluric as tl
from .config import shapes_dir


def _first(x):
    return next(iter(x))


def get_site_aoi(site_name, shapes_dir=shapes_dir):
    path = os.path.join(shapes_dir, '{}_poly.shp'.format(site_name))
    feature = _first(tl.FileCollection.open(path))
    return feature.geometry
