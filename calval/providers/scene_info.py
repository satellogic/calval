"""
Module should contain the base SceneInfo class, plus other stuff which is useful
for implementing the provider-specific specializations
"""
import os
import datetime as dt
import collections
import warnings
import calval.config


scaling = collections.namedtuple('scaling', ['multiply', 'add'])
noscale = scaling(1, 0)


def extract_archive(input_path, output_path, mkdir, opener):
    """
    `output_path` should contain the full folder name of the scene, as it should appear
    after extraction.

    If `mkdir` is specified, then `output_path` folder is created, and the
    archive is extracted there.

    Otherwise it is assumed that the archive contains relative paths (including the base
    folder name), so the archive is opened in the dirname `output_path`.
    In this case the basename of the path is only used for checking if it existed before.
    """
    if os.path.isdir(output_path):
        warnings.warn('{} already exists, not extracting'.format(output_path))
        return

    if mkdir:
        os.mkdir(output_path)
    else:
        output_path = os.path.dirname(output_path)

    with opener(input_path) as archive:
        archive.extractall(output_path)


class SceneInfo:
    """
    Base class for provider-specific scene information.
    Should contain the basic metadata required for opening the scenes, (such as tile
    location, product and date).
    The info can mostly be deduced from the filenames of the archived file.
    """
    config = dict(
        data_dir=calval.config.data_dir,
        scenes=None,
        archives=calval.config.dl_dir,
        normalized=calval.config.normalized_dir
    )
    product_units = {
        'sr': None, 'toa': None
    }

    def __init__(self, config):
        if config is not None:
            self.config = config

    def _data_path(self, name):
        path = self.config.get(name)
        if path is None:
            path = os.path.join(self.config['data_dir'], name)
        return path

    # funcs for generating normalized paths

    def _path_params(self, product=None, timestamp=None, tag='0'):
        # We allow specifying product in order to support computed products
        if product is None:
            product = self.product
        else:
            assert product in self.products

        # We allow specifying timestamp for cases where the filename does not
        # contain the hour
        if timestamp is None:
            timestamp = self.timestamp
        else:
            assert timestamp.date() == self.timestamp.date()
            # If tz aware: enforce UTC
            if timestamp.tzinfo is not None:
                timestamp = timestamp.astimezone(dt.timezone.utc)
        ts = timestamp.strftime('%Y%m%d%H%M')
        return [product, self.satellite, self.tile_id, ts, tag]

    def blob_prefix(self, *args, **kwargs):
        return '/'.join(self._path_params(*args, **kwargs))

    def fname_prefix(self, *args, **kwargs):
        return '_'.join(self._path_params(*args, **kwargs))

    @classmethod
    def from_filename(cls, filename, config=None):
        for c in cls.__subclasses__():
            scene_info = c.from_filename(filename, config)
            if scene_info is not None:
                return scene_info
        raise ValueError('Unknown filename format: {}'.format(filename))

    @classmethod
    def from_foldername(cls, foldername, config=None):
        for c in cls.__subclasses__():
            scene_info = c.from_foldername(foldername, config)
            if scene_info is not None:
                return scene_info
        raise ValueError('Unknown foldername format: {}'.format(foldername))

    @property
    def scenes_path(self):
        return self._data_path('scenes')

    @property
    def archives_path(self):
        return self._data_path('archives')

    def archive_path(self):
        return os.path.join(self.archives_path, self.archive_filename())

    def scene_path(self):
        return os.path.join(self.scenes_path, self.scene_filename())

    def is_archive(self):
        return os.path.isfile(self.archive_path())

    def is_scene(self):
        return os.path.isdir(self.scene_path())
