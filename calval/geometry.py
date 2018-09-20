try:
    from math import isclose
except ImportError:  # pragma: no cover
    def isclose(a, b, rel_tol=1e-9, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


class IncidenceAngle:
    accuracy = 1e-3

    def __init__(self, azimuth_deg, elevation_deg):
        self.azimuth = azimuth_deg
        self.elevation = elevation_deg

    @classmethod
    def from_dict(cls, d):
        return cls(d['azimuth'], d['elevation'])

    @property
    def zenith(self):
        return 90 - self.elevation

    def __repr__(self):
        return 'IncidenceAngle({}, {})'.format(self.azimuth, self.elevation)

    def __str__(self):
        return str((self.azimuth, self.elevation))

    def to_dict(self):
        return {'azimuth': self.azimuth, 'elevation': self.elevation}

    def isclose(self, other, accuracy):
        eq = (isclose(self.azimuth, other.azimuth, abs_tol=accuracy) and
              isclose(self.elevation, other.elevation, abs_tol=accuracy))
        return eq

    def __eq__(self, other):
        return self.isclose(other, self.accuracy)
