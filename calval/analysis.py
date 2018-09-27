import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyspectral.solar import SolarIrradianceSpectrum, TOTAL_IRRADIANCE_SPECTRUM_2000ASTM


def integrate(site_measurements, srf):
    """
    integrate site measurement over given SRF
    :param site_measurements: radcalnet.SiteMeasurement
    :param srf: SRF
    :return: 4x TimeSeries: toa, toa_errs, sr, sr_errs
    """
    def _integrate(measurements_df, srf):
        measured_spectrum = [float(c) for c in measurements_df.columns]
        srf_interpolated = np.nan_to_num(srf(measured_spectrum))  # interpolated to wavelengths of site measurements
        integrated_values = {time: np.dot(srf_interpolated, np.nan_to_num(row.values))
                             for time, row in measurements_df.iterrows()}
        return pd.Series(data=integrated_values).astype(np.float32)

    return [_integrate(getattr(site_measurements, data), srf)
            for data in ['toa', 'toa_errs', 'sr', 'sr_errs']]


def exatmospheric_irradiance(srf, dlambda_nm=0.5, start_nm=200.0, end_nm=2000.0):
    """
    Compute the exatmospheric solar irradiance of some sensor (band) at 1a.u.
    :param srf: SRF
    `dlambda_nm`, `start_nm`, `end_nm`: interpolation parameters for the solar spectrum
    :return: band irradiance at 1au, in [W/(m^2 um)]
    """
    warnings.warn(DeprecationWarning(
        '`exatmospheric_irradiance` is scheduled to be removed, '
        'use `srf_exatmospheric_irradiance` (nm based units) instead.'))
    srr = SolarIrradianceSpectrum(TOTAL_IRRADIANCE_SPECTRUM_2000ASTM, dlambda=dlambda_nm/1000)
    srr.interpolate(ival_wavelength=(start_nm/1000, end_nm/1000))
    lambdas = srr.ipol_wavelength * 1000
    response = srf(lambdas)
    avg = np.dot(response, srr.ipol_irradiance) / np.sum(response)
    return avg


def srf_exatmospheric_irradiance(srf, dlambda_nm=0.5, start_nm=200.0, end_nm=2000.0):
    """
    Compute the exatmospheric solar irradiance of some sensor (band) at 1a.u.
    :param srf: SRF
    `dlambda_nm`, `start_nm`, `end_nm`: interpolation parameters for the solar spectrum
    :return: band irradiance at 1au, in [W/(m^2 nm)]
    """
    srr = SolarIrradianceSpectrum(TOTAL_IRRADIANCE_SPECTRUM_2000ASTM, dlambda=dlambda_nm/1000)
    srr.interpolate(ival_wavelength=(start_nm/1000, end_nm/1000))
    lambdas = srr.ipol_wavelength * 1000
    values = srr.ipol_irradiance / 1000.0
    response = srf(lambdas)
    avg = np.dot(response, values) / np.sum(response)
    return avg


def plot(types, site_measurements, srfs, with_errors=True, fig=None, show=True):
    """
    plots simulated TOA or SR, based on site measurements, and camera spectral response
    :param types: 'toa' or 'sr' or ['toa', 'sr']
    :param site_measurements: SiteMeasurements
    :param srfs: list of SRF
    :param with_errors: if True =- shows error bars
    :param fig:
    :param show: if True - draws plot
    :return: plt figure
    """

    def _plot(data, err, with_errors, label):
        if with_errors:
            artists = plt.errorbar(data.index.values, data.values, yerr=err)
            artists.lines[0].set_label(label)
        else:
            artists = plt.plot(data.index.values, data.values)
            artists[0].set_label(label)

    if fig is None:
        fig = plt.figure()
    for srf in srfs:
        # for type in types:
        if 'toa' in types or 'toa' == types:
            data, err = integrate(site_measurements, srf)[:2]
            _plot(data, err, with_errors=with_errors, label='%s %s TOA' % (srf.satellite, srf.band))
        if 'sr' in types or 'sr' == types:
            data, err = integrate(site_measurements, srf)[2:4]
            _plot(data, err, with_errors=with_errors, label='%s %s SR' % (srf.satellite, srf.band))

    fig.autofmt_xdate()
    plt.title('Reflectance in %s' % site_measurements.meta['site'])
    plt.grid()
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.tight_layout()
    if show:  # pragma: no cover
        plt.show()
    return fig


def toa_irradiance_to_reflectance(irradiance, sun_band_flux, sun_locator, time, sat_angle=None,
                                  ignore_sun_zenith=False):
    """
    Computes toa reflectance from toa_irradiance
    :param irradiance: toa irradiance in [W/(m^2 nm sr)].
    :param sun_band_flux: The sun spectral flux at 1au in [W/(m^2 nm)]
       (to compute from band SRF, use the function `srf_exatmospheric_irradiance`).
    :param sun_locator: `SunLocator` object for the relevant location on earth.
    :param time: timezone-aware datetime.
    :param sat_angle: `IncidenceAngle` of satellite relative to the site.
       if not specified, assume to be at zenith.
    :param ignore_sun_zenith: If true, ignore the correction due to sun elevation.
       This is used for comparing to the raw TOA values of Landsat8 L1C product
    """
    if ignore_sun_zenith:
        sun_irrad = sun_locator.direct_normal_irradiance(time, base_flux=sun_band_flux)
    else:
        sun_irrad = sun_locator.direct_horizontal_irradiance(time, base_flux=sun_band_flux)
    if sat_angle is not None:
        sun_irrad = sun_irrad * np.sin(sat_angle.elevation * np.pi / 180)
    return np.pi * irradiance / sun_irrad
