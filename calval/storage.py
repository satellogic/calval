"""
Abstraction of queryable storage for NormalizedScenes
"""
import os
import glob
import itertools as it
import calval.config
from calval.normalized_scene import FilebasedScene, NormalizedSceneId


def _filestorage_glob_patterns(**kwargs):
    terms = [kwargs.pop(field, '*')
             for field in NormalizedSceneId.tuple_type._fields]
    assert not kwargs, 'Unrecognized field names: {}'.format(kwargs)

    # terms which are not str are assumed to contain choices (list of str)
    choice_inds = [i for i, val in enumerate(terms) if not isinstance(val, str)]
    val_lists = [terms[i][:] for i in choice_inds]

    patterns = []
    for values in it.product(*val_lists):
        for i, ind in enumerate(choice_inds):
            terms[ind] = values[i]
        patterns.append(os.path.sep.join(terms))
    return patterns


class FileStorage:
    def __init__(self, base_dir=calval.config.normalized_dir):
        self.base_dir = base_dir

    def query(self, **kwargs):
        scenes = []
        for pattern in _filestorage_glob_patterns(**kwargs):
            for path in glob.glob(os.path.join(self.base_dir, pattern)):
                scenes.append(FilebasedScene(path))
        return scenes
