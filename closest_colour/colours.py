import re
from typing import Dict, Tuple, List

from colormath.color_conversions import convert_color
from colormath.color_objects import ColorBase, sRGBColor, LabColor
from scipy.spatial import KDTree
import webcolors


HEX_COLOUR_RE = re.compile(r"#(?P<R>[0-9a-fA-F]{2})(?P<G>[0-9a-fA-F]{2})(?P<B>[0-9a-fA-F]{2})")


# I needed some example colours to test with. Since CSS defines a nice list of colours,
# I found a Python module which lists them in a convenient format, and used that
# as the list of colours to compare to. There are ~150 of them, which is probably
# a realistic number to make sure performance is OK.
def webcolors_to_ours(source: Dict[str, str] = webcolors.CSS3_NAMES_TO_HEX) -> List[Tuple[str, sRGBColor]]:
    our_colours = []
    for name, hex_colour in source.items():
        match = HEX_COLOUR_RE.match(hex_colour)
        if not match:
            raise ValueError(f"could not parse webcolors colour '{name}' = '{hex_colour}'")
        floats = [int(match.group(g), base=16) / 255.0 for g in ("R", "G", "B")]
        our_colours.append((name, sRGBColor(*floats)))
    return our_colours


# Here, instead of using webcolors_to_ours(), we could define our own list of colours.
# Or we could define them in Django settings, or similar.

OUR_COLOURS_LIST = webcolors_to_ours()
OUR_COLOURS_DICT = dict(OUR_COLOURS_LIST)


def colour_to_srgb_floats(colour: ColorBase) -> Tuple[float, float, float]:
    if isinstance(colour, sRGBColor):
        return colour.rgb_r, colour.rgb_g, colour.rgb_b
    else:
        return colour_to_srgb_floats(convert_color(colour, sRGBColor))


def create_kdtree(colours: Dict[str, ColorBase]) -> KDTree:
    colour_array = [colour_to_srgb_floats(colour) for name, colour in colours.items()]
    return KDTree(colour_array)


OUR_SRGB_KDTREE = create_kdtree(OUR_COLOURS_DICT)
OUR_LAB_KDTREE = create_kdtree({name: convert_color(colour, LabColor) for name, colour in OUR_COLOURS_DICT.items()})


def nearest_colour_name(target: ColorBase, kdtree=OUR_LAB_KDTREE) -> str:
    distance, index = kdtree.query(colour_to_srgb_floats(target), k=1)
    return OUR_COLOURS_LIST[index][0]
