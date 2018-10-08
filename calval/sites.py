import os
import telluric as tl
import calval.config


def _first(x):
    return next(iter(x))


def get_site_aoi(site_name, shapes_dir=None):
    if shapes_dir is None:
        shapes_dir = calval.config.shapes_dir
    path = os.path.join(shapes_dir, '{}_poly.shp'.format(site_name))
    feature = _first(tl.FileCollection.open(path))
    return feature.geometry
