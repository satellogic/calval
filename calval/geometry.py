import math


class IncidenceAngle:
    accuracy = 1e-3

    def __init__(self, azimuth_deg, elevation_deg):
        self.azimuth = azimuth_deg
        self.elevation = elevation_deg

    @property
    def zenith(self):
        return 90 - self.elevation

    def __repr__(self):
        return 'IncidenceAngle({}, {})'.format(self.azimuth, self.elevation)

    def __str__(self):
        return str((self.azimuth, self.elevation))

    def isclose(self, other, accuracy):
        eq = (math.isclose(self.azimuth, other.azimuth, abs_tol=accuracy) and
              math.isclose(self.elevation, other.elevation, abs_tol=accuracy))
        return eq

    def __eq__(self, other):
        return self.isclose(other, self.accuracy)
