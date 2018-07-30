"""
Module should contain the base SceneInfo class, plus othe stuff which is useful for implementing
the provider-specific specializations
"""
import os
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
        archives=calval.config.dl_dir
    )

    def __init__(self, config):
        if config is not None:
            self.config = config

    def _data_path(self, name):
        path = self.config.get(name)
        if path is None:
            path = os.path.join(self.config['data_dir'], name)
        return path

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
