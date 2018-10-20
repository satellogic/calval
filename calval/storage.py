"""
Abstraction of queryable storage for NormalizedScenes
"""
import os
import glob
import itertools as it
import calval.config
from calval.normalized_scene import FilebasedScene, NormalizedSceneId


def glob_patterns(separator=os.path.sep, **kwargs):
    """
    Convert list of keyword args to a list of glob patterns.
    keys are field names of the NormalizedSceneId (product, satellite, tile_id, ...)
    values of the keys can be either a single string or a list of choices.
    For example:

    >>> glob_patterns(product=['sr', 'toa'], satellite='S2A')
    ['sr/S2A/*/*/*', 'toa/S2A/*/*/*']
    """
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
        patterns.append(separator.join(terms))
    return patterns


class FileStorage:
    def __init__(self, base_dir=calval.config.normalized_dir):
        self.base_dir = base_dir

    def query(self, **kwargs):
        scenes = []
        for pattern in glob_patterns(**kwargs):
            for path in glob.glob(os.path.join(self.base_dir, pattern)):
                scenes.append(FilebasedScene(path))
        return scenes
