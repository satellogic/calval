import os
import glob
import pytest
from datetime import datetime

import numpy as np

import calval.batch_plot  # noqa: F401
from radcalnet.site_measurements import SiteMeasurements
from calval.satellites.srf import SRF, Sentinel2Green, Sentinel2Blue
from calval.analysis import integrate, plot


def test_integrate():
    srf = SRF(500, 530, [.2, .3, .4, .5])
    pathlist = glob.glob(os.path.join('tests', 'data', 'datastore', 'BTCN', '*'))
    sm = SiteMeasurements.from_pathlist(pathlist)[datetime(2018, 5, 28, 4, 0): datetime(2018, 5, 28, 5, 0)]
    toa, toa_errs, sr, sr_errs = integrate(sm, srf)

    sr_std = np.std(sr.values)  # due to proximity in time, most of variance should come from measurements noise
    sr_expected_std = np.mean(sr_errs.values)
    assert sr_std == pytest.approx(sr_expected_std, rel=0.1)


def test_plot():
    pathlist = glob.glob(os.path.join('tests', 'data', 'datastore', 'BTCN', '*'))
    sm = SiteMeasurements.from_pathlist(pathlist)[datetime(2018, 5, 28): datetime(2018, 5, 29)]
    srfs = [Sentinel2Blue(), Sentinel2Green()]
    # make sure all below modes don't fail:
    for with_errors in [False, True]:
        for types in ['toa', 'sr', ['toa', 'sr']]:
            plot(types, sm, srfs, with_errors=with_errors)
