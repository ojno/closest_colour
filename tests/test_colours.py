import random

import pytest
from colormath.color_conversions import convert_color
from colormath.color_objects import LabColor, sRGBColor

from closest_colour.colours import (
    ColourMatcher,
    LabKDTreeColourMatcher,
    SRGBKDTreeColourMatcher,
    webcolors_to_ours,
)

# use the CSS2 colours as a small test case
TEST_COLOURS_SRGB = {
    "aqua": sRGBColor(0.0, 1.0, 1.0),
    "black": sRGBColor(0.0, 0.0, 0.0),
    "blue": sRGBColor(0.0, 0.0, 1.0),
    "fuchsia": sRGBColor(1.0, 0.0, 1.0),
    "green": sRGBColor(0.0, 128 / 255, 0.0),
    "gray": sRGBColor(128 / 255, 128 / 255, 128 / 255),
    "lime": sRGBColor(0.0, 1.0, 0.0),
    "maroon": sRGBColor(128 / 255, 0.0, 0.0),
    "navy": sRGBColor(0.0, 0.0, 128 / 255),
    "olive": sRGBColor(128 / 255, 128 / 255, 0.0),
    "purple": sRGBColor(128 / 255, 0.0, 128 / 255),
    "red": sRGBColor(1.0, 0.0, 0.0),
    "silver": sRGBColor(192 / 255, 192 / 255, 192 / 255),
    "teal": sRGBColor(0.0, 128 / 255, 128 / 255),
    "white": sRGBColor(1.0, 1.0, 1.0),
    "yellow": sRGBColor(1.0, 1.0, 0.0),
}


def test_webcolors_to_ours() -> None:
    test_colours_hex = {
        "aqua": "#00ffff",
        "black": "#000000",
        "blue": "#0000ff",
        "fuchsia": "#ff00ff",
        "green": "#008000",
        "gray": "#808080",
        "lime": "#00ff00",
        "maroon": "#800000",
        "navy": "#000080",
        "olive": "#808000",
        "purple": "#800080",
        "red": "#ff0000",
        "silver": "#c0c0c0",
        "teal": "#008080",
        "white": "#ffffff",
        "yellow": "#ffff00",
    }
    actual_colours = webcolors_to_ours(test_colours_hex)
    assert actual_colours.keys() == TEST_COLOURS_SRGB.keys()
    for name, colour in actual_colours.items():
        # sRGBColor doesn't support equality, so check the value tuples instead
        assert colour.get_value_tuple() == TEST_COLOURS_SRGB[name].get_value_tuple()


def test_webcolors_to_ours_invalid() -> None:
    invalid_colours_hex = {
        "octarine": "wharblgarbl",
    }
    with pytest.raises(ValueError):
        webcolors_to_ours(invalid_colours_hex)


def test_colour_to_floats_matching() -> None:
    srgb_colour = sRGBColor(random.random(), random.random(), random.random())
    assert ColourMatcher.colour_to_floats(srgb_colour, sRGBColor) == srgb_colour.get_value_tuple()


def test_colour_to_floats_non_matching() -> None:
    srgb_colour = sRGBColor(random.random(), random.random(), random.random())
    lab_colour = convert_color(srgb_colour, LabColor)
    assert ColourMatcher.colour_to_floats(srgb_colour, LabColor) == lab_colour.get_value_tuple()


@pytest.mark.parametrize(
    "matcher", (SRGBKDTreeColourMatcher(TEST_COLOURS_SRGB), LabKDTreeColourMatcher(TEST_COLOURS_SRGB))
)
def test_colour_matcher_sanity_identical(matcher: ColourMatcher) -> None:
    for name, colour in TEST_COLOURS_SRGB.items():
        assert matcher.nearest(colour)[0] == name


@pytest.mark.parametrize(
    "matcher", (SRGBKDTreeColourMatcher(TEST_COLOURS_SRGB), LabKDTreeColourMatcher(TEST_COLOURS_SRGB))
)
def test_colour_matcher_sanity_nearby(matcher: ColourMatcher) -> None:
    for name, colour in TEST_COLOURS_SRGB.items():
        red, green, blue = colour.get_value_tuple()
        red += random.uniform(-0.1, 0.1)
        green += random.uniform(-0.1, 0.1)
        blue += random.uniform(-0.1, 0.1)
        perturbed_colour = sRGBColor(red, green, blue)
        assert matcher.nearest(perturbed_colour)[0] == name
