from calval.scene_utils import make_sceneinfo, make_sat_measurements
from calval.sat_measurements import SatMeasurements


def get_filenames():
    return [line.rstrip() for line in open('scene_list.txt')]


if (1):
    # satellites = #['landsat8', 'sentinel2']
    site_name = 'negev'
    filenames = get_filenames()
    scene_infos = (make_sceneinfo(scene) for scene in filenames)
    for info in scene_infos:
        print(info.archive_filename())
    product = 'toa'
    # sm1 = make_sat_measurements(scene_infos, site_name, product)
    sm1 = make_sat_measurements(filenames, site_name, product)
    print(sm1.df)
    sm1.plot()
    # df.to_csv('{}_{}_landsat8.csv'.format(site_name, product))
    # df.to_csv('{}_{}_sentinel2.csv'.format(site_name, product))
if (1):
    product = 'sr'
    sm2 = make_sat_measurements(filenames, site_name, product)
    print(sm2.df)
    sm2.plot()
    # df.to_csv('{}_{}_landsat8.csv'.format(site_name, product))
    # df.to_csv('{}_{}_sentinel2.csv'.format(site_name, product))
    import matplotlib.pyplot
    matplotlib.pyplot.show()

# plot existing csv fgiles
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
