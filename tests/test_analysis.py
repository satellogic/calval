import os
import datetime as dt
import glob
import numpy as np
import pytest

import calval.batch_plot  # noqa: F401
from radcalnet.site_measurements import SiteMeasurements
from calval.sun_locator import SunLocator
from calval.geometry import IncidenceAngle
from calval.satellites.srf import (
    SRF, Sentinel2Green, Sentinel2Blue, Landsat8Blue, Landsat8Green, Landsat8Red, Landsat8Nir)
from calval.analysis import (
    integrate, plot, exatmospheric_irradiance, srf_exatmospheric_irradiance,
    toa_irradiance_to_reflectance)


def test_integrate():
    srf = SRF(500, 530, [.2, .3, .4, .5])
    pathlist = glob.glob(os.path.join('tests', 'data', 'datastore', 'BTCN', '*'))
    sm = SiteMeasurements.from_pathlist(pathlist)[dt.datetime(2018, 5, 28, 4, 0): dt.datetime(2018, 5, 28, 5, 0)]
    toa, toa_errs, sr, sr_errs = integrate(sm, srf)

    sr_std = np.std(sr.values)  # due to proximity in time, most of variance should come from measurements noise
    sr_expected_std = np.mean(sr_errs.values)
    assert sr_std == pytest.approx(sr_expected_std, rel=0.1)


def test_exatmospheric_irradiance():
    # compare results to info from
    # https://en.wikipedia.org/wiki/Landsat_8#Operational_Land_Imager
    landsat_irradiances = [1.925, 1.826, 1.574, 0.955]
    for i, srf_class in enumerate([Landsat8Blue, Landsat8Green, Landsat8Red, Landsat8Nir]):
        irradiance = srf_exatmospheric_irradiance(srf_class())
        with pytest.warns(DeprecationWarning):
            um_irradiance = exatmospheric_irradiance(srf_class())
        assert um_irradiance / 1000.0 == pytest.approx(irradiance)
        ref_value = landsat_irradiances[i]
        assert irradiance == pytest.approx(ref_value, rel=0.03)


def test_plot():
    pathlist = glob.glob(os.path.join('tests', 'data', 'datastore', 'BTCN', '*'))
    sm = SiteMeasurements.from_pathlist(pathlist)[dt.datetime(2018, 5, 28): dt.datetime(2018, 5, 29)]
    srfs = [Sentinel2Blue(), Sentinel2Green()]
    # make sure all below modes don't fail:
    for with_errors in [False, True]:
        for types in ['toa', 'sr', ['toa', 'sr']]:
            plot(types, sm, srfs, with_errors=with_errors)


def test_toa_irradiance_to_reflectance():
    site_lon, site_lat = (35.0089, 30.1135)
    locator = SunLocator(site_lon, site_lat)
    # estimations from SRF of Landsat8 Blue, Green, Red:
    band_sun_flux = [1.96907, 1.84787, 1.56946]
    # some data from landsat products of negev site
    times = [
        dt.datetime(*x, tzinfo=dt.timezone.utc) for x in [
            (2018, 5, 15, 8, 10, 30), (2018, 5, 31, 8, 10, 17),
            (2018, 6, 16, 8, 10, 24), (2018, 7, 2, 8, 10, 34)
        ]]
    band_irradiance = [0.165804666, 0.203901788, 0.2303557377]
    band_reflectance = [0.26356, 0.35174, 0.47122]
    blue_irradiance = [0.165804666, 0.163292076, 0.160111839, 0.157002668]
    blue_reflectance = [0.26356, 0.26108, 0.25702, 0.25244]

    # sanity of sat_position dependance
    time = times[0]
    sunflux = band_sun_flux[0]
    irradiance = band_irradiance[0]
    ref_default = toa_irradiance_to_reflectance(
            irradiance, sunflux, locator, time)

    def calc_at(elevation):
        return toa_irradiance_to_reflectance(
            irradiance, sunflux, locator, time, IncidenceAngle(0, elevation))

    reflectance = calc_at(90)
    assert reflectance == pytest.approx(ref_default)
    assert calc_at(80) > reflectance
    assert calc_at(20) > calc_at(40)

    # verify for each band in one product
    time = times[0]
    for i, sunflux in enumerate(band_sun_flux):
        reflectance = toa_irradiance_to_reflectance(
            band_irradiance[i], sunflux, locator, time,
            ignore_sun_zenith=True)
        assert reflectance == pytest.approx(band_reflectance[i], rel=0.03)
        reflectance_correct = toa_irradiance_to_reflectance(
            band_irradiance[i], sunflux, locator, time)
        assert reflectance < reflectance_correct < 1.0

    # verify blue band in several products
    sunflux = band_sun_flux[0]
    for i, time in enumerate(times):
        reflectance = toa_irradiance_to_reflectance(
            blue_irradiance[i], sunflux, locator, time,
            ignore_sun_zenith=True)
        assert reflectance == pytest.approx(blue_reflectance[i], rel=0.03)
        reflectance_correct = toa_irradiance_to_reflectance(
            blue_irradiance[i], sunflux, locator, time)
        assert reflectance < reflectance_correct < 1.0
