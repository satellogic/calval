try:
    from functools import cached_property
except ImportError:
    # For python<3.8, provide mini (non-threadsafe) implementation
    class cached_property:
        def __init__(self, function):
            self._function = function

        def __get__(self, obj, _=None):
            value = self._function(obj)
            setattr(obj, self._function.__name__, value)
            return value
