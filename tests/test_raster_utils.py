import os
import shutil
import glob
import numpy as np
from testing_utils import config
from calval.raster_utils import TileCache, hires_tile, asfloat

green_url = os.path.join(
    config['scenes'],
    'S2A_MSIL1C_20180526T081601_N0206_R121_T36RXU_20180526T120617.SAFE'
    '/GRANULE/L1C_T36RXU_A015276_20180526T081919/IMG_DATA/T36RXU_20180526T081601_B03.jp2')
tile_coords = (2446, 1688, 12)


def test_hires_tile():
    tile = hires_tile(green_url, tile_coords)
    assert tile.shape == (1, 256, 256)
    tile_float = hires_tile(green_url, tile_coords, decode=True)
    assert tile_float.dtype == np.float64
    # validate the transofrmation
    assert np.all(tile.image.mask == tile_float.image.mask)
    assert np.ma.allclose(tile.image / (1 << 16), tile_float.image)
    # test asfloat()
    assert tile_float == asfloat(tile)


def test_cache(temp_dir):
    cache = TileCache(os.path.join(temp_dir, 'cache'))
    assert len(glob.glob(os.path.join(cache.folder, '*.tif'))) == 0
    # copy the raster to the temp dir
    target_path = os.path.join(temp_dir, os.path.basename(green_url))
    shutil.copyfile(green_url, target_path)
    # open target using cache
    tile = hires_tile(target_path, tile_coords, tile_coords[2] + 1,
                      get_tile=cache.get_tile)
    assert tile.shape == (1, 512, 512)
    assert len(glob.glob(os.path.join(cache.folder, '*.tif'))) == 4
    # remove the target, open again using cache
    os.remove(target_path)
    tile = hires_tile(target_path, tile_coords, tile_coords[2] + 1,
                      get_tile=cache.get_tile)
    assert tile.shape == (1, 512, 512)
