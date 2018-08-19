from collections import OrderedDict
import dateutil.parser


def read_mtl(path):
    context = OrderedDict()
    stack = [('/', context)]
    for line in open(path, 'rt'):
        if line.strip().lower() == 'end':
            break

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
