import pytest
import testing_utils
from mercantile import parent
from calval.sites import site_names, site_tile


def test_site_names():
    assert site_names() == ['negev']
    assert len(site_names(testing_utils.original_shapes_dir)) > 1


def test_site_tile():
    shapes_dir = testing_utils.original_shapes_dir
    assert site_tile('negev', 10) == site_tile('negev', 10, shapes_dir)
    for site in site_names(shapes_dir):
        if site == 'rrvalley':
            # railroad valley on tile intersection - not supported yet
            with pytest.raises(AssertionError):
                tile = site_tile(site, shapes_dir=shapes_dir)
        else:
            tile = site_tile(site, shapes_dir=shapes_dir)
            assert parent(tile) == site_tile(site, 12, shapes_dir)
