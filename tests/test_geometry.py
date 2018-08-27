from calval.geometry import IncidenceAngle

az, el = 77.8, 76.2


def test_incidence_angle():
    pos = IncidenceAngle(az, el)
    assert eval(repr(pos), globals()) == pos
    assert eval(str(pos)) == (az, el)
    assert pos.zenith == 90 - el
