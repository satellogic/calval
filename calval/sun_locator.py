import warnings
import datetime as dt
import numpy as np
import pysolar.solartime as stime
from pysolar.solar import get_sun_earth_distance, get_position
from pysolar.tzinfo_check import check_aware_dt
from calval.geometry import IncidenceAngle

solar_constant = 1361.5  # from wikipedia
_s2_julian_epoch_t = dt.datetime(1950, 1, 1, 0, 0, tzinfo=dt.timezone.utc).timestamp()


@check_aware_dt('time')
def sun_earth_distance(time):
    # TODO, get rid of this filtering once pysolar updates leapsecond data
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', "I don't know about leap seconds after")
        jde = stime.get_julian_ephemeris_day(time)
        jce = stime.get_julian_ephemeris_century(jde)
        jme = stime.get_julian_ephemeris_millennium(jce)
    return get_sun_earth_distance(jme)


def s2_julian_day(timestamp, delta):
    return (timestamp - _s2_julian_epoch_t)/(3600*24) + delta


# * formula taken from:
#   https://sentinel.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-1c/algorithm
#   (equation 2)
# * 0.0172 is probably 2*pi/365.25 = 0.0172024
# * definition of julian day unclear (delta=3 assumed via fit to spa sun distance in 2018)
def s2_earth_sun_distance(timestamp, julian_delta=3):
    return 1 - 0.01673 * np.cos(0.0172 * (s2_julian_day(timestamp, julian_delta) - 2))


class SunLocator:
    """
    Compute sun position, distance and related attributes, relative to a fixed
    position on earth.
    Methods of this class take as input a timezone-aware datetime object.
    """
    def __init__(self, longitude, latitude, elevation=0):
        self.longitude = longitude
        self.latitude = latitude
        self.elevation = elevation

    @check_aware_dt('time')
    def position(self, time):
        """
        :return: position of the sun, as `IncidenceAngle` object
        """
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore', "I don't know about leap seconds after 2017")
            az, el = get_position(self.latitude, self.longitude, time,
                                  self.elevation)
        return IncidenceAngle(az, el)

    def distance_au(self, time):
        """
        :return: Earth-Sun distance, in astronomical units.
        """
        return sun_earth_distance(time)

    @check_aware_dt('time')
    def s2_distance_au(self, time):
        """
        Simpler formula for sun-distance.
        """
        return s2_earth_sun_distance(time.timestamp())

    def direct_normal_irradiance(self, time, base_flux=solar_constant):
        """
        `base_flux` is the value of the relevant irradiance at 1 a.u. from the sun.
        The default is the solar constant (representing total irradiance).
        :return: exatmospheric DNI
        """
        return base_flux / self.distance_au(time) ** 2

    def direct_horizontal_irradiance(self, time, base_flux=solar_constant):
        return self.direct_normal_irradiance(time, base_flux) *\
            np.sin(self.position(time).elevation * np.pi / 180)
