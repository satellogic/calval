import numpy as np


# Spectral Response Function, providing response per wavelength
class SRF:

    def __init__(self, start, end, response):
        """

        :param start: wavelength of response[0], in [nm]
        :param end: wavelength of response[0], in [nm]
        :param response: [response]. spacing is derived automatically
        """
        self.start = start
        self.end = end
        self.response = response
        self.wavelengths = np.linspace(self.start, self.end, len(self.response))

    @property
    def spacing(self):
        return self.wavelengths[1] - self.wavelengths[0]

    def __getitem__(self, wavelength):
        """
        calculate SRF at specified wavelength (using linear interpolation) .
        :param wavelength: single value or array. in [nm]
        :return: single value or array of responses
        """
        return np.interp(wavelength, self.wavelengths, self.response)
