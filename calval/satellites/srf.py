import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


band_colors = {'blue': 'b', 'green': 'g', 'red': 'r', 'nir': 'k'}
satellite_styles = {'landsat8': 'o-', 'sentinel2': 'd--', 'newsat': 'd-'}


# Spectral Response Function, providing response per wavelength
class SRF:

    def __init__(self, start, end, response, satellite=None, band=None):
        """

        :param start: wavelength of response[0], in [nm]
        :param end: wavelength of response[0], in [nm]
        :param response: [response]. spacing is derived automatically
        :param satellite: satellite name, e.g. 'landsat8'. optional
        :param band: band name, e.g. 'red'. optional
        """
        self.start = start
        self.end = end
        self.response = response
        self.wavelengths = np.linspace(self.start, self.end, len(self.response))
        self.satellite = satellite or ''
        self.band = band or ''

    def __call__(self, wavelength):
        """
        calculate SRF at specified wavelength (using linear interpolation).
        :param wavelength: single value or array. in [nm]
        :return: single value or array of responses. returns np.nan if outside the range
        """
        return np.interp(wavelength, self.wavelengths, self.response, left=np.nan, right=np.nan)

    @property
    def spacing(self):
        return self.wavelengths[1] - self.wavelengths[0]

    @property
    def bandwidth(self):
        return self.end - self.start

    @property
    def center(self):
        return (self.start + self.end) / 2

    def as_dataframe(self):
        return pd.DataFrame({'response': list(self.response)}, columns=['response'], index=self.wavelengths)


class Sentinel2Blue(SRF):
    def __init__(self):
        # taken from https://github.com/robintw/Py6S/blob/master/Py6S/Params/wavelength.py#L612
        super().__init__(0.45500, 0.53000,
                         [0.00903, 0.06152, 0.29220, 0.38410, 0.40016, 0.43699, 0.50532, 0.53212,
                          0.53466, 0.55070, 0.60197, 0.61734, 0.57586, 0.54412, 0.57168, 0.65330,
                          0.73840, 0.77085, 0.78836, 0.81658, 0.84498, 0.83295, 0.78694, 0.76370,
                          0.81003, 0.92817, 1.00000, 0.81615, 0.28699, 0.08400, 0.02508, ],
                         'sentinel2', 'blue')


class Sentinel2Green(SRF):
    def __init__(self):
        # taken from https://github.com/robintw/Py6S/blob/master/Py6S/Params/wavelength.py#L621
        super().__init__(0.53750, 0.58250,
                         [0.00861, 0.08067, 0.45720, 0.82804, 0.89007, 0.86027, 0.83333, 0.86773,
                          0.95043, 1.00000, 0.96410, 0.86866, 0.80267, 0.78961, 0.83845, 0.85799,
                          0.50599, 0.09829, 0.00826, ],
                         'sentinel2', 'green')


class Sentinel2Red(SRF):
    def __init__(self):
        # taken from https://github.com/robintw/Py6S/blob/master/Py6S/Params/wavelength.py#L628
        super().__init__(0.64750, 0.68250,
                         [0.09225, 0.81775, 0.99038, 0.99545, 0.95701, 0.81417, 0.76998, 0.83083,
                          0.89627, 0.95593, 0.97240, 0.96571, 0.91448, 0.42297, 0.04189],
                         'sentinel2', 'red')



def plot_srfs(srfs, colors=band_colors, styles=satellite_styles, fig=None, title=None, show=False):
    """
    plots multiple SRFs
    :param srfs: [SRF]
    :param colors: { band_name -> plt color }, e.g. {'red': 'r'}. optional
    :param styles:  { satellite_name -> plt style }, e.g. {'landsat8': 'o-'}. optional
    :param fig: plt.figure
    :param title:
    :param show: if true - shows the plt.figure
    :return: plt.figure
    """
    if fig is None:
        fig = plt.figure()
    for srf in srfs:
        df = srf.as_dataframe()
        if len(df) > 0:
            style = colors.get(srf.band, '') + styles.get(srf.satellite, '')
            artists = plt.plot(df, style)
            artists[0].set_label('{}_{}'.format(srf.satellite, srf.band))

    fig.autofmt_xdate()
    plt.title(title or 'Spectral Response Functions')
    plt.grid()
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.tight_layout()
    if show:
        plt.show()

    return fig
