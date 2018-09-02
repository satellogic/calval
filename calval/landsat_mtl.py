import datetime as dt
from collections import OrderedDict

import dateutil.parser
import pandas as pd


# TODO: rename to parse_odl_file or similar (MTL & ANG files are both in ODL format)
def read_mtl(path):
    context = OrderedDict()
    stack = [('/', context)]
    unfinished_list_val = None
    for line in open(path, 'rt'):
        if line.strip().lower() == 'end':
            break

        if unfinished_list_val is not None:
            val = line.strip()
            if val.endswith(')'):
                val = unfinished_list_val + val
                context[tag] = eval('[{}]'.format(val[1:-1]))  # noqa: F821
                unfinished_list_val = None
            else:
                assert val.endswith(',')
                unfinished_list_val = unfinished_list_val + val
            continue

        tag, val = line.strip().split('=')
        tag = tag.rstrip()
        val = val.lstrip()

        if tag.lower() == 'group':
            assert val not in context
            context[val] = OrderedDict()
            context = context[val]
            stack.append((val, context))
        elif tag.lower() == 'end_group':
            while stack[-1][0] != val:
                del stack[-1]
            del stack[-1]
            context = stack[-1][1]

        elif val.startswith('"'):
            assert val.endswith('"')
            context[tag] = val[1:-1]
        elif val.startswith('('):
            if val.endswith(')'):
                # TODO: avoid eval (should be list specific)
                context[tag] = eval('[{}]'.format(val[1:-1]))
            else:
                assert val.endswith(',')
                unfinished_list_val = val
        elif '.' in val:
            context[tag] = float(val)
        elif ':' in val or val.count('-') > 1:
            context[tag] = dateutil.parser.parse(val)
        else:
            context[tag] = int(val)
    # end lines loop
    while stack[-1][0] != '/':
        del stack[-1]
    context = stack[-1][1]
    return context


def ephemeris_df(angles_metadata):
    """
    Read the EPHEMERIS block of the angles metadata file
    """
    data = angles_metadata['EPHEMERIS']
    epoch = dt.datetime.strptime(
        '{}-{}'.format(data['EPHEMERIS_EPOCH_YEAR'], data['EPHEMERIS_EPOCH_DAY']),
        '%Y-%j') + dt.timedelta(seconds=data['EPHEMERIS_EPOCH_SECONDS'])
    epoch = epoch.replace(tzinfo=dt.timezone.utc)
    n = data['NUMBER_OF_POINTS']
    vals = data['EPHEMERIS_TIME']
    assert len(vals) == n
    d = {}
    d['time'] = [epoch + dt.timedelta(seconds=t) for t in vals]
    for c in ['X', 'Y', 'Z']:
        vals = data['EPHEMERIS_ECEF_' + c]
        assert len(vals) == n
        d[c] = vals
    df = pd.DataFrame(d)
    return df.set_index('time')
