import datetime as dt
import dateutil.parser
import numpy as np
from pytest import approx
from calval.sun_position import SunPosition

UTC = dt.timezone.utc
test_lat = 32.0627972
test_lon = 34.8150253

sunpos = SunPosition(test_lon, test_lat, 0)

position_ref = [  # time, zenith, azimuth
    ('2018-08-01T07:00:00+03:00', 77.832660, 76.154671),
    ('2018-08-01T10:00:00+03:00', 40.066391, 100.251030),
    ('2018-08-01T13:00:00+03:00', 14.384801, 192.458194),
    ('2018-08-01T19:00:00+03:00', 83.132815, 286.926466),
]


def test_position():
    for t_str, zenith, azimuth in position_ref:
        time = dateutil.parser.parse(t_str)
        pos = sunpos.position(time)
        assert np.allclose([pos.zenith, pos.azimuth], [zenith, azimuth], rtol=1e-3)


def test_distance():
    start_date = dt.datetime(2018, 1, 1, tzinfo=UTC)
    for day in range(0, 365*2):
        time = start_date + dt.timedelta(days=day)
        assert sunpos.distance_au(time) == approx(sunpos.s2_distance_au(time), rel=1e-3)


def test_irradiance():
    # irradiance value and sanity at given date (near the perihelion)
    tz = dt.timezone(dt.timedelta(hours=2))
    neartime = dt.datetime(2018, 1, 3, 12, 30, tzinfo=tz)
    delta = dt.timedelta(hours=2)
    assert sunpos.direct_normal_irradiance(neartime) == approx(1408, rel=1e-3)
    assert (sunpos.direct_normal_irradiance(neartime + delta) ==
            approx(sunpos.direct_normal_irradiance(neartime), rel=1e-4))
    assert (sunpos.direct_normal_irradiance(neartime) >
            sunpos.direct_horizontal_irradiance(neartime))
    assert (sunpos.direct_horizontal_irradiance(neartime + delta) <
            sunpos.direct_horizontal_irradiance(neartime))
    assert (sunpos.direct_horizontal_irradiance(neartime - delta) <
            sunpos.direct_horizontal_irradiance(neartime))

    # compare to the aphelion
    fartime = dt.datetime(2018, 7, 4, 12, 30, tzinfo=tz)
    assert sunpos.direct_normal_irradiance(neartime) > sunpos.direct_normal_irradiance(fartime)

    # times one year later
    neartime2 = dt.datetime(2019, 1, 3, 12, 30, tzinfo=tz)
    fartime2 = dt.datetime(2019, 7, 4, 12, 30, tzinfo=tz)
    assert sunpos.direct_normal_irradiance(neartime) == approx(sunpos.direct_normal_irradiance(neartime2), rel=1e-3)
    assert sunpos.direct_normal_irradiance(fartime) == approx(sunpos.direct_normal_irradiance(fartime2), rel=1e-3)
