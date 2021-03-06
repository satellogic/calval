import os
import logging
import numpy as np
import telluric as tl

# TODO: Temporary imports for uploading scenes. seperate out cloud backend dependencies
from tqdm import tqdm
from azure.storage.blob import BlockBlobService

from calval.normalized_scene import band_names
from calval.providers import SceneInfo, SceneData
# Import provider module to enable the factory mechanism
import calval.providers.sentinel  # noqa: F401
import calval.providers.landsat  # noqa: F401
from calval.scene_utils import make_sat_measurements
from calval.sat_measurements import SatMeasurements


logger = logging.getLogger()
logger.getChild('calval').setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(levelname)-4s] %(name)-4s: %(message)s'))
logger.addHandler(handler)


def get_filenames():
    return [line.rstrip() for line in open('scene_list.txt')]


if (True):
    filenames = get_filenames()
    scene_infos = [SceneInfo.from_filename(scene) for scene in filenames]
    for info in scene_infos:
        print(info.archive_filename())

runit = True
if (runit):
    # satellites = #['landsat8', 'sentinel2']
    site_name = 'negev'
    product = 'toa'
    # sm1 = make_sat_measurements(scene_infos, site_name, product)
    sm1 = make_sat_measurements(filenames, site_name, product, correct_landsat_toa=True)
    print(sm1.df)
    sm1.plot()
    # df.to_csv('{}_{}_landsat8.csv'.format(site_name, product))
    # df.to_csv('{}_{}_sentinel2.csv'.format(site_name, product))
if (runit):
    # Note: Irradiance only available for landsat
    product = 'irradiance'
    # sm1 = make_sat_measurements(scene_infos, site_name, product)
    sm3 = make_sat_measurements(filenames, site_name, product)
    print(sm3.df)
    sm3.plot()

    sm4 = make_sat_measurements(filenames, site_name, 'computed_toa')
    print(sm4.df)
    fig = sm4.plot(legend_label='calc')
    sm1_ls = make_sat_measurements(filenames, site_name, 'toa', provider='landsat8')
    sm1_ls.plot(styles={'landsat8': '+--'}, fig=fig)

    sm5 = make_sat_measurements(filenames, site_name, 'computed_toa_corrected')
    print(sm5.df)
    fig = sm5.plot(legend_label='calc')
    sm6 = make_sat_measurements(filenames, site_name, 'toa', provider='landsat8',
                                correct_landsat_toa=True)
    sm6.plot(styles={'landsat8': '+--'}, fig=fig)
if (runit):
    product = 'sr'
    sm2 = make_sat_measurements(filenames, site_name, product)
    print(sm2.df)
    sm2.plot()
    # df.to_csv('{}_{}_landsat8.csv'.format(site_name, product))
    # df.to_csv('{}_{}_sentinel2.csv'.format(site_name, product))
    import matplotlib.pyplot
    matplotlib.pyplot.show()

# some metadata analysis (sentinel)
if (runit):
    s_l1 = [i for i in scene_infos if i.provider == 'sentinel2' and i.product == 'toa']
    s_l2 = [i for i in scene_infos if i.provider == 'sentinel2' and i.product == 'sr']
    scene = SceneData.from_sceneinfo(s_l1[0])
    print('s2 l1 si timestamp:', scene.sceneinfo.timestamp)
    print('s2 l1 timestamp:', scene.timestamp)
    print('s2 l1 sun angle:', scene.sun_average_angle)
    print('s2 l1 sat angle:', scene.sat_average_angle)
    scene = SceneData.from_sceneinfo(s_l2[0])
    print('s2 l2 timestamp:', scene.timestamp)
    print('s2 l2 sun angle:', scene.sun_average_angle)
    print('s2 l2 sat angle:', scene.sat_average_angle)

# some metadata analysis (landsat)
if (runit):
    ls_l1 = [i for i in scene_infos if i.provider == 'landsat8' and i.product == 'toa']
    ls_l2 = [i for i in scene_infos if i.provider == 'landsat8' and i.product == 'sr']
    si = ls_l1[0]
    scene = SceneData.from_sceneinfo(si)
    print('ls l1 si timestamp:', scene.sceneinfo.timestamp)
    print('ls l1 timestamp:', scene.timestamp)
    print('ls l1 sun angle:', scene.sun_average_angle)
    print('ls l1 computed sun angle:', scene.center_sunpos.position(scene.timestamp))
    print('ls l1 sun distance:', scene.earth_sun_distance)
    print('ls l1 computed sun distance:', scene.center_sunpos.distance_au(scene.timestamp))
    print('ls l1 sat angle:', scene.sat_average_angle)
    print('ls l1 roll:', scene.roll_angle)
    print('ls l1 esd:', scene.earth_sun_distance)
    print('ls l1 cloud cover:', scene.cloud_cover)
    print('ls l1 satellite coords:', scene.sat_coords)
    scene2 = SceneData.from_sceneinfo(ls_l2[0])
    print('ls l1 timestamp:', scene2.timestamp)
    print('ls l2 sun angle:', scene2.sun_average_angle)
    print('ls l2 computed sun angle:', scene2.center_sunpos.position(scene2.timestamp))
    print('ls l2 sun distance:', scene2.earth_sun_distance)
    print('ls l2 computed sun distance:', scene2.center_sunpos.distance_au(scene2.timestamp))
    print('ls l2 sat angle:', scene2.sat_average_angle)

# testing stuff (remove that)
if (1):
    scenes_l8 = [SceneData.from_sceneinfo(x) for x in scene_infos
                 if x.provider == 'landsat8' and x.product == 'toa' and x.tile_id == '174039']
    scene_l8 = scenes_l8[1]
    # print('saving {}'.format(scene_l8.get_metadata_path('irradiance')))
    # scene_l8.save_normalized(product='irradiance')
    # print('saving {}'.format(scene_l8.get_metadata_path()))
    # scene_l8.save_normalized()
    scenes_s2 = [SceneData.from_sceneinfo(x) for x in scene_infos
                 if x.provider == 'sentinel2' and x.product == 'toa' and x.tile_id == 'T36RXU']
    scene_s2 = scenes_s2[6]
    # print('saving {}'.format(scene_s2.get_metadata_path()))
    # scene_s2.save_normalized()


class TqdmUpTo(tqdm):
    """Provides `update_to(n, total)` which uses `tqdm.update(delta_n)`."""
    def update_to(self, current, total):
        self.update(current - self.n)


def upload_normalized(scene, bands, product):
    from azure.storage.common.retry import (
        # ExponentialRetry,
        LinearRetry,
        # no_retry
    )
    connection_string = open('/home/amit/telluric/secrets/azure-storage-connection-string').read().rstrip()
    svc = BlockBlobService(connection_string=connection_string)
    svc.retry = LinearRetry(max_attempts=20).retry
    container = 'calval'

    blob_prefix = scene.sceneinfo.blob_prefix(product, scene.timestamp)
    fname_prefix = scene.sceneinfo.fname_prefix(product, scene.timestamp)
    for band in bands:
        local_path = scene.get_normalized_path(band, product=product)
        filelen = os.stat(local_path).st_size
        blob_name = '{}/{}_{}.tif'.format(blob_prefix, fname_prefix, band)
        with TqdmUpTo(unit='B', unit_scale=True, miniters=1, total=filelen,
                      desc=blob_name) as t:
            svc.create_blob_from_path(
                container, blob_name, local_path,
                progress_callback=t.update_to)

    local_path = scene.get_metadata_path(product)
    filelen = os.stat(local_path).st_size
    blob_name = '{}/{}_metadata.json'.format(blob_prefix, fname_prefix)
    with TqdmUpTo(unit='B', unit_scale=True, miniters=1, total=filelen,
                  desc=blob_name) as t:
        svc.create_blob_from_path(
            container, blob_name, local_path,
            progress_callback=t.update_to)


if (0):
    connection_string = open('/home/amit/telluric/secrets/azure-storage-connection-string').read().rstrip()
    svc = BlockBlobService(connection_string=connection_string)

# Upload normalized scenes
if (0):
    # scene = scenes_l8[2]
    # upload_normalized(scene, band_names, 'toa')
    for scene in []:  # scenes_l8[3:]:
        print('saving', scene.sceneinfo.scene_id)
        scene.save_normalized()
        print('uploading...')
        upload_normalized(scene, band_names, 'toa')

    scene = scenes_s2[2]
    upload_normalized(scene, band_names, 'toa')
    for scene in scenes_s2[3:]:
        print('saving', scene.sceneinfo.scene_id)
        scene.save_normalized()
        print('uploading...')
        upload_normalized(scene, band_names, 'toa')


if (0):
    connection_string = open(
        '/home/amit/telluric/secrets/azure-storage-connection-string').read().rstrip()
    svc = BlockBlobService(connection_string=connection_string)
    container = 'calval'
    # all = list(svc.list_blobs(container))
    band = 'blue'
    product = 'toa'
    print(scene_s2._normalized_dirname(product))
    blob_prefix = scene_s2.sceneinfo.blob_prefix(product, scene_s2.timestamp)
    print(blob_prefix)
    fname_prefix = scene_s2.sceneinfo.fname_prefix(product, scene_s2.timestamp)
    local_path = scene_s2.get_normalized_path(band, product=product)
    filelen = os.stat(local_path).st_size
    print('--->', local_path, filelen)
    blob_name = '{}/{}_{}.tif'.format(blob_prefix, fname_prefix, band)
    print(blob_name)
    print('--->', scene_s2.get_metadata_path('toa'))
    print('{}/{}_metadata.json'.format(blob_prefix, fname_prefix))
    with TqdmUpTo(unit='B', unit_scale=True, miniters=1, total=filelen,
                  desc=blob_name) as t:
        svc.create_blob_from_path(
            container, blob_name,  local_path,
            progress_callback=t.update_to)

if (0):
    pairs = {}
    for band in band_names:
        print('saving band: {}'.format(band))
        l8_tile = tl.GeoRaster2.open(scene_l8.get_normalized_path(band)).get_tile(2446, 1688, 12)
        l8_tile.save('/tmp/l8_tile_{}.tif'.format(band), nodata=0)
        s2_tile = tl.GeoRaster2.open(scene_s2.get_normalized_path(band)).get_tile(2446, 1688, 12)
        s2_tile.save('/tmp/s2_tile_{}.tif'.format(band), nodata=0)
        pairs[band] = [np.ravel(l8_tile.image[0]), np.ravel(s2_tile.image[0])]
if (0):
    import matplotlib.pyplot as plt
    l8_tile = tl.GeoRaster2.open(scene_l8.get_normalized_path('blue')).get_tile(2446, 1688, 12)
    s2_tile = tl.GeoRaster2.open(scene_s2.get_normalized_path('blue')).get_tile(2446, 1688, 12)
    x, y = [np.ma.ravel(x.image) / 65536.0 for x in [l8_tile, s2_tile]]
    plt.figure()
    plt.plot(x, y, ',')
    plt.plot([0.15, 0.35], [0.15, 0.35], 'k-')
    plt.xlabel('l8')
    plt.ylabel('s2')
    plt.grid(True)

# some spectral plots
if (0):
    import numpy as np
    import matplotlib.pyplot as plt
    from calval.satellites.srf import Sentinel2Green, Sentinel2Red, Landsat8Blue, NewsatBlue, NewsatRed
    from pyspectral.solar import (SolarIrradianceSpectrum, TOTAL_IRRADIANCE_SPECTRUM_2000ASTM)
    srr = SolarIrradianceSpectrum(TOTAL_IRRADIANCE_SPECTRUM_2000ASTM, dlambda=0.0005)
    srr.interpolate(ival_wavelength=(0.200, 2.000))
    print(srr.units)
    print(srr.ipol_wavelength, srr.ipol_irradiance)

    plt.figure()
    plt.plot(srr.ipol_wavelength, srr.ipol_irradiance, 'k-.')
    srf = Sentinel2Green()
    x = srr.ipol_wavelength * 1000
    vals = srf(x) * srr.ipol_irradiance
    avg = np.dot(srf(x), srr.ipol_irradiance) / np.sum(srf(x))
    plt.plot(srr.ipol_wavelength, vals, 'g-')
    plt.plot([srf.start/1000, srf.end/1000], [avg, avg], 'g--')

    srf = Sentinel2Red()
    x = srr.ipol_wavelength * 1000
    vals = srf(x) * srr.ipol_irradiance
    avg = np.dot(srf(x), srr.ipol_irradiance) / np.sum(srf(x))
    plt.plot(srr.ipol_wavelength, vals, 'r-')
    plt.plot([srf.start/1000, srf.end/1000], [avg, avg], 'r--')

    srf = Landsat8Blue()
    x = srr.ipol_wavelength * 1000
    vals = srf(x) * srr.ipol_irradiance
    avg = np.dot(srf(x), srr.ipol_irradiance) / np.sum(srf(x))
    plt.plot(srr.ipol_wavelength, vals, 'b-')
    plt.plot([srf.start/1000, srf.end/1000], [avg, avg], 'b--')

    srf = NewsatBlue()
    x = srr.ipol_wavelength * 1000
    vals = srf(x) * srr.ipol_irradiance
    avg = np.dot(srf(x), srr.ipol_irradiance) / np.sum(srf(x))
    plt.plot(srr.ipol_wavelength, vals, 'b-')
    plt.plot([srf.start/1000, srf.end/1000], [avg, avg], 'bx-')

    srf = NewsatRed()
    x = srr.ipol_wavelength * 1000
    vals = srf(x) * srr.ipol_irradiance
    avg = np.dot(srf(x), srr.ipol_irradiance) / np.sum(srf(x))
    plt.plot(srr.ipol_wavelength, vals, 'r-')
    plt.plot([srf.start/1000, srf.end/1000], [avg, avg], 'rx-')

# plot existing csv files
if (0):
    site, product = 'negev', 'toa'
    path = '{}_{}_sentinel2.csv'.format(site, product)
    sm1 = SatMeasurements.from_csvfile(path)
    sm1.plot()
    site, product = 'negev', 'sr'
    path = '{}_{}_sentinel2.csv'.format(site, product)
    sm2 = SatMeasurements.from_csvfile(path)
    sm2.plot()
    import matplotlib.pyplot
    matplotlib.pyplot.show()
