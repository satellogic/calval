import pytest
from testing_utils import normalize_folders_into
from calval.storage import FileStorage


def test_filestorage(temp_dir):
    normalize_folders_into(temp_dir)
    storage = FileStorage(temp_dir)
    # query all
    scenes = storage.query()
    assert len(scenes) == 4
    # complex query
    scenes = storage.query(satellite='LC08', product=['sr', 'toa'])
    assert len(scenes) == 3
    for s in scenes:
        assert s['satellite_name'] == 'LC08'
        assert s['productname'] in {'sr', 'toa'}
    # invalid queries
    scenes = storage.query(satellite=['dummy1', 'dummy2'])
    assert len(scenes) == 0
    with pytest.raises(AssertionError) as excinfo:
        scenes = storage.query(nonexistant='blah')
    assert 'Unrecognized field' in str(excinfo)
