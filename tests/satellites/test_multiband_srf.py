import pytest

import numpy as np

import calval.utils.batch_plot  # noqa: F401
from calval.satellites.srf import Sentinel2Blue, Sentinel2Green, Sentinel2Red
from calval.satellites.multiband_srf import Sentinel2SRF, Newsat3HyperSpectralSRF


def test_sentinel2():
    multiband = Sentinel2SRF()
    band_srfs = [cls() for cls in [Sentinel2Blue, Sentinel2Green, Sentinel2Red]]
    assert np.allclose(multiband.by_band['blue'].response, Sentinel2Blue().response)
    for i, single_srf in enumerate(band_srfs):
        assert multiband.srfs[i].mean == pytest.approx(single_srf.mean)
        assert np.allclose(multiband.srfs[i].wavelengths, single_srf.wavelengths)


def test_hyperspectral():
    multiband = Newsat3HyperSpectralSRF()
    for i, single_srf in enumerate(multiband.srfs):
        desc, w, units = single_srf.band.split('_')
        assert (desc, units) == ('HyperCube', 'nm')
        wavelength = float(w)
        assert abs(wavelength - single_srf.mean) < 1
