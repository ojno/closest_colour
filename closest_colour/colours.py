import re
from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Type, TypeVar, Generic

from colormath.color_conversions import convert_color
from colormath.color_objects import ColorBase, sRGBColor, LabColor
from scipy.spatial import KDTree
import webcolors


HEX_COLOUR_RE = re.compile(r"#(?P<R>[0-9a-fA-F]{2})(?P<G>[0-9a-fA-F]{2})(?P<B>[0-9a-fA-F]{2})")


def webcolors_to_ours(source: Dict[str, str] = webcolors.CSS3_NAMES_TO_HEX) -> Dict[str, sRGBColor]:
    our_colours = {}
    for name, hex_colour in source.items():
        match = HEX_COLOUR_RE.match(hex_colour)
        if not match:
            raise ValueError(f"could not parse webcolors colour '{name}' = '{hex_colour}'")
        floats = [int(match.group(g), base=16) / 255.0 for g in ("R", "G", "B")]
        our_colours[name] = sRGBColor(*floats)
    return our_colours


# In [30]: timeit.timeit(lambda: colours.nearest_colour_name(sRGBColor(random.random(), random.random(), random.random())
#     ...: ), number=100000) / 100000.0
# Out[30]: 6.836906400043517e-05
#
# => on my hardware, matching a colour to its nearest in the list with this approach
#    runs more than 100000 times per second. This is unlikely to be a bottleneck.


class ColourMatcher(ABC):
    @staticmethod
    def colour_to_floats(colour: ColorBase, colour_type: Type[ColorBase]) -> Tuple[float, ...]:
        if isinstance(colour, colour_type):
            return colour.get_value_tuple()
        else:
            return ColourMatcher.colour_to_floats(convert_color(colour, colour_type), colour_type)

    @abstractmethod
    def nearest(self, target: ColorBase) -> Tuple[str, float]:
        pass


class KDTreeColourMatcher(ColourMatcher):
    def __init__(self, colours: Dict[str, ColorBase], colour_type: Type[ColorBase]):
        self.colour_type = colour_type
        self.colours_list = [(name, convert_color(colour, colour_type)) for name, colour in colours.items()]
        self.colours_array = [ColourMatcher.colour_to_floats(colour, colour_type) for name, colour in self.colours_list]
        self.kdtree = KDTree(self.colours_array)

    def nearest(self, target: ColorBase) -> Tuple[str, float]:
        distance, index = self.kdtree.query(ColourMatcher.colour_to_floats(target, self.colour_type), k=1)
        return self.colours_list[index][0], distance


class LabKDTreeColourMatcher(KDTreeColourMatcher):
    def __init__(self, colours: Dict[str, ColorBase]):
        super().__init__(colours, LabColor)


class SRGBKDTreeColourMatcher(KDTreeColourMatcher):
    def __init__(self, colours: Dict[str, ColorBase]):
        super().__init__(colours, sRGBColor)
