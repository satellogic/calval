import numpy as np
import pandas as pd


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
