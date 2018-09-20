import re
import xml.etree.ElementTree as ET
import dateutil.parser

float_re = re.compile(r'\d+\.\d+$')


def additem(d, key, value):
    """
    sets `d[key] = value`, but if `d` already has a value at key,
    make it a list and append at the end.
    """
    if key in d:
        if not isinstance(d[key], list):
            d[key] = [d[key]]
        d[key].append(value)
    else:
        d[key] = value


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
            if name == 'SOLAR_IRRADIANCE':
                name = '{}_{}'.format(
                    name, element.attrib['bandId'])
                value = float(element.text)
            elif name == 'EXT_POS_LIST':
                value = [float(x) for x in value.split()]
            elif name == 'MASK_FILENAME':
                if 'bandId' in element.attrib:
                    name = '{}_{}_{}'.format(
                        name, element.attrib['type'], element.attrib['bandId'])
                else:
                    name = '{}_{}'.format(name, element.attrib['type'])
                value = element.text
            # In General_Info we have time fields
            elif name.endswith('_TIME') and value[4] == '-':
                value = dateutil.parser.parse(value)
            # In Geometric_Info we have angle fields
            elif name.endswith('_ANGLE'):
                d[name + '_unit'] = element.attrib['unit']
                value = float(value)
            else:
                # (value may be None)
                if value and float_re.match(value):
                    value = float(value)
            additem(d, name, value)
        # container elements
        else:
            # In Tile_Angles we have grid fields
            if name.endswith('_Grid') or name.endswith('_Grids'):
                if name.endswith('s'):
                    name = '{}_{}_{}'.format(
                        name, element.attrib['bandId'], element.attrib['detectorId'])
                value = elements2grids(element)
            # In Tile_Angles we have angle lists
            elif name.endswith('_Angle_List'):
                value = elements2anglelist(element)
            # In Tile_Geocoding we have by-resolution info:
            elif name in {'Size', 'Geoposition'}:
                name = '{}_{}'.format(name, element.attrib['resolution'])
                value = elements2dict(element)
            else:
                value = elements2dict(element)
            additem(d, name, value)
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


def parse_xml_metadata(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    blocks = {}
    for block in root:
        name = block.tag.split('}')[-1]
        blocks[name] = elements2dict(block)
    return blocks
