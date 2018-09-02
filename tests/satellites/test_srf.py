import pytest

import numpy as np

import calval.batch_plot  # noqa: F401
from calval.satellites.srf import \
    (SRF, PerfectSRF, Sentinel2Red, Sentinel2Green, Sentinel2Blue, plot_srfs,
     Landsat8Blue, Landsat8Green, Landsat8Red, Landsat8Nir,
     NewsatBlue, NewsatGreen, NewsatRed, NewsatNir, NewsatPan)


def test_srf_interpolates_correctly():
    start, end = 1, 21  # step of 10nm
    response = [3, 4, 5]
    srf = SRF(start, end, response)
    assert srf(start) == response[0]
    assert srf(end) == response[-1]
    assert srf(start + 2.5) == .75 * response[0] + .25 * response[1]
    assert np.allclose(srf([start, end]), [response[0], response[-1]])
    assert srf.spacing == 10
    assert np.isnan(srf(start - 1, outside_value=np.nan))
    assert np.isnan(srf(end + 1, outside_value=np.nan))
    assert np.allclose([srf(start-1), srf(end+1)], 0)


def test_basic():
    perfect = PerfectSRF(100, 200)
    assert perfect.bandwidth == 100


def test_as_dataframe():
    srf = Sentinel2Green()
    df = srf.as_dataframe()
    assert df['response'][srf.start] == srf(srf.start)


def test_sentinel():
    # comparing central wavelength to https://en.wikipedia.org/wiki/Sentinel-2
    assert Sentinel2Blue().center == pytest.approx(490, abs=10)
    assert Sentinel2Green().center == pytest.approx(560, abs=.10)
    assert Sentinel2Red().center == pytest.approx(665, abs=10)


def test_landsat():
    # Check spacing (to avoid type/copy errors)
    assert Landsat8Blue().spacing == 1
    assert Landsat8Green().spacing == 1
    assert Landsat8Red().spacing == 1
    assert Landsat8Nir().spacing == 1
    # comparing central wavelength to
    # https://landsat.gsfc.nasa.gov/wp-content/uploads/2014/09/Ball_BA_RSR.v1.2.xlsx
    assert Landsat8Blue().mean == pytest.approx(482.04, rel=0.002)
    assert Landsat8Green().mean == pytest.approx(561.41, rel=1e-3)
    assert Landsat8Red().mean == pytest.approx(654.59, rel=1e-3)
    assert Landsat8Nir().mean == pytest.approx(864.67, rel=1e-3)


def test_newsat():
    # comparing spacing is indeed 1pix
    for srf in [NewsatBlue, NewsatGreen, NewsatRed, NewsatNir, NewsatPan]:
        assert srf().spacing == pytest.approx(1)


def test_plot():
    # checks plot_srf doesn't fail
    srfs = [Sentinel2Red(), Sentinel2Green(), Sentinel2Blue()]
    plot_srfs(srfs, show=False)
