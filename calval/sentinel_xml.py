import xml.etree.ElementTree as ET
import dateutil.parser


def elements2anglelist(elements):
    anglelist = {}
    for element in elements:
        name = '{}_{}'.format(element.tag, element.attrib['bandId'])
        val = {}
        for item in element:
            assert item.tag.endswith('_ANGLE')
            val[item.tag] = float(item.text)
            val[item.tag + '_unit'] = item.attrib['unit']
        anglelist[name] = val
    return anglelist


def parse_grid(elements):
    grid = {}
    for element in elements:
        name = element.tag
        if name in {'COL_STEP', 'ROW_STEP'}:
            grid[name] = float(element.text)
            grid[name + '_unit'] = element.attrib['unit']
        elif name == 'Values_List':
            values = []
            for row in element:
                assert row.tag == 'VALUES'
                values.append([float(x) for x in row.text.split()])
            grid[name] = values
        else:
            raise ValueError('Unrecognized grid tag: {}'.format(name))
    return grid


def elements2grids(elements):
    return {
        element.tag: parse_grid(element)
        for element in elements
    }


def elements2dict(elements):
    d = {}
    for element in elements:
        name = element.tag
        # if leaf element
        if len(element) == 0:
            value = element.text
            # In Quality_Indicators_Info we have mask filename lists
            if name == 'MASK_FILENAME':
                if 'bandId' in element.attrib:
                    name = '{}_{}_{}'.format(
                        name, element.attrib['type'], element.attrib['bandId'])
                else:
                    name = '{}_{}'.format(name, element.attrib['type'])
                d[name] = element.text
            # In General_Info we have time fields
            elif name.endswith('_TIME') and value[4] == '-':
                value = dateutil.parser.parse(value)
                d[name] = value
            # In Geometric_Info we have angle fields
            elif name.endswith('_ANGLE'):
                d[name] = float(value)
                d[name + '_unit'] = element.attrib['unit']
            else:
                d[name] = value
        # container elements
        else:
            # In Tile_Angles we have grid fields
            if name.endswith('_Grid') or name.endswith('_Grids'):
                if name.endswith('s'):
                    name = '{}_{}_{}'.format(name, element.attrib['bandId'], element.attrib['detectorId'])
                d[name] = elements2grids(element)
            # In Tile_Angles we have angle lists
            elif name.endswith('_Angle_List'):
                d[name] = elements2anglelist(element)
            # In Tile_Geocoding we have by-resolution info:
            elif name in {'Size', 'Geoposition'}:
                name = '{}_{}'.format(name, element.attrib['resolution'])
                d[name] = elements2dict(element)
            else:
                d[name] = elements2dict(element)
        # end 'if leaf element'
    return d


def parse_tile_metadata(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    blocks = {}
    for block in root:
        name = block.tag.split('}')[-1]
        if name == 'General_Info':
            blocks[name] = elements2dict(block)
        elif name == 'Geometric_Info':
            blocks[name] = elements2dict(block)
        elif name == 'Quality_Indicators_Info':
            blocks[name] = elements2dict(block)
    return blocks
