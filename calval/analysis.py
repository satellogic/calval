import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.switch_backend('Agg')


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

    return [_integrate(getattr(site_measurements, data), srf) for data in ['toa', 'toa_errs', 'sr', 'sr_errs']]


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
    try:
        plt.tight_layout()
    except ValueError:  # https://github.com/matplotlib/matplotlib/issues/5456
        pass
    if show:
        plt.show()
    return fig
