import numpy as np

from calval.satellites.srf import SRF


def test_srf_interpolates_correctly():
    start, end = 1, 21  # step of 10nm
    response = [3, 4, 5]
    srf = SRF(start, end, response)
    assert srf[start] == response[0]
    assert srf[end] == response[-1]
    assert srf[start + 2.5] == .75 * response[0] + .25 * response[1]
    assert np.allclose(srf[[start, end]], [response[0], response[-1]])
    assert srf.spacing == 10
