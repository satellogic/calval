import os
import re

import matplotlib.pyplot as plt
import pandas as pd
from calval.normalized_scene import band_names

# band_names = ['B', 'G', 'R', 'NIR']  # old names (keep comment until fixed)
band_colors = 'bgrk'
provider_styles = {'landsat8': 'o-', 'sentinel2': 'd--'}


class SatMeasurements:
    """
    Contains a DataFrame with measurements (mean, median, std) of some product
    (TOA or Surface reflectivity) for a given site.
    Stores also the names of the product and the site, and optionally some user defined
    label describing this instance of data.
    Labels are used for plot titles and for default filenames.
    """
    fname_fmt = '{site}_{product}.csv'
    fname_fmt_label = fname_fmt[:-4] + '_{label}.csv'
    fname_re = re.compile(fname_fmt.replace(
        '{', '(?P<').replace('}', '>.*)')
    )
    fname_label_re = re.compile(fname_fmt_label.replace(
        '{', '(?P<').replace('}', '>.*)')
    )

    def __init__(self, df, site, product, label=None):
        self.df = df
        self.site, self.product, self.label = site, product, label

    @classmethod
    def from_csvfile(cls, filepath, site=None, product=None, label=None):
        """
        Builds the SatMeasurements object from a csv file.
        if `site` and `product` are not specified directly, they are extracted from the
        filename (as well of the user-defined label, if available in filename).
        """
        fname = os.path.basename(filepath)
        if site is None or product is None:
            # Try to extract site and product from filename
            m = cls.fname_label_re.match(fname)
            if m is None:
                m = cls.fname_re.match(fname)
            if m is not None:
                d = m.groupdict()
                site, product = d['site'], d['product']
                if label is None:
                    label = d['label']
        assert None not in {site, product}, "must specify site and product"
        df = pd.read_csv(filepath, parse_dates=[0], index_col=0)
        return cls(df, site, product, label)

    @property
    def fname(self):
        fmt = self.fname_fmt if self.label is None else self.fname_fmt_label
        return fmt.format(site=self.site, product=self.product, label=self.label)

    def write(self, dir=None, label=None):
        if label is not None:
            self.label = label
        path = self.fname
        if dir is not None:
            path = os.path.join(dir, path)
        self.df.to_csv(path)

    def plot(self, band_names=band_names,
             band_colors=band_colors, styles=provider_styles,
             fig=None, legend_label=None):
        if fig is None:
            fig = plt.figure()
        for provider in provider_styles.keys():
            provider_df = self.df[self.df['provider'] == provider]
            if len(provider_df) > 0:
                for i, band in enumerate(band_names):
                    chan = provider_df['{}_median'.format(band)]
                    std = provider_df['{}_std'.format(band)]
                    artists = plt.errorbar(chan.index.values, chan.values, yerr=std,
                                           fmt=band_colors[i] + styles[provider])
                    label = '{}_{}'.format(provider, band)
                    if legend_label is not None:
                        label = '{} {}'.format(label, legend_label)
                    artists.lines[0].set_label(label)

        fig.autofmt_xdate()
        if self.label:
            title = '{} {} ({})'.format(self.site, self.product, self.label)
        else:
            title = '{} {}'.format(self.site, self.product)
        plt.title(title)
        plt.grid(True)
        plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        plt.tight_layout()
        return fig
