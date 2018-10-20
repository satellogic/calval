"""
This module is a hack in order to avoid errors in case of batch plotting (e.g. in tests),
where there is no interactive environment properly configured (e.g. in containers).

Usage: `from calval.utils.batch_plot import plt`
Make sure this line comes before importing any third-party package which depends on
`matplotlib.pyplot`

See also http://stackoverflow.com/questions/2801882/
"""
import matplotlib
matplotlib.use('Agg', warn=False, force=False)
import matplotlib.pyplot as plt  # noqa: E402, F401
