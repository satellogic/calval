class IncidenceAngle:
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
