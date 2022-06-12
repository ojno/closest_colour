from typing import List, Optional

import numpy
import pytest
from colormath.color_objects import sRGBColor
from django.conf import settings

from closest_colour.images import (
    ImageColourSummariser,
    KMeansImageColourSummariser,
    MeanImageColourSummariser,
)


@pytest.mark.parametrize("resize_to", (1, None))
@pytest.mark.parametrize(
    "filename,colour_floats",
    (("1x1white.png", [1.0, 1.0, 1.0]), ("1x1black.png", [0.0, 0.0, 0.0])),
)
def test_image_file_to_numpy_array_1x1(filename: str, colour_floats: List[float], resize_to: Optional[int]) -> None:
    image_file = open(settings.BASE_DIR / "images" / filename, "rb")
    array = ImageColourSummariser.image_file_to_numpy_array(image_file, resize_to=resize_to)
    assert numpy.array_equal(array, numpy.asarray([[colour_floats]]))


def test_image_file_to_numpy_array_200x200() -> None:
    image_file = open(settings.BASE_DIR / "images" / "1x1white.png", "rb")
    array = ImageColourSummariser.image_file_to_numpy_array(image_file)
    assert numpy.array_equal(array, numpy.ones((200, 200, 3)))


@pytest.mark.parametrize("summariser", (MeanImageColourSummariser(), KMeansImageColourSummariser()))
@pytest.mark.parametrize(
    "filename,expected_colour",
    (("1x1white.png", sRGBColor(1.0, 1.0, 1.0)), ("1x1black.png", sRGBColor(0.0, 0.0, 0.0))),
)
def test_image_summariser_sanity_1x1(
    filename: str, expected_colour: sRGBColor, summariser: ImageColourSummariser
) -> None:
    image_file = open(settings.BASE_DIR / "images" / filename, "rb")
    actual_colour = summariser.summarise(image_file)
    assert actual_colour.get_value_tuple() == expected_colour.get_value_tuple()


@pytest.mark.parametrize(
    "filename,expected_colour",
    (
        ("test-sample-black.png", sRGBColor(0.18888637254894014, 0.18888637254894014, 0.18888676470580287)),
        ("test-sample-grey.png", sRGBColor(0.2629755882351811, 0.3147582352940076, 0.3777171568628979)),
        ("test-sample-navy.png", sRGBColor(0.060355294117644655, 0.060355294117644655, 0.3518944117645697)),
        ("test-sample-teal.png", sRGBColor(0.05832803921568428, 0.4173357843135801, 0.46189784313721066)),
    ),
)
def test_mean_image_summariser_regression(filename: str, expected_colour: sRGBColor) -> None:
    summariser = MeanImageColourSummariser()
    image_file = open(settings.BASE_DIR / "images" / filename, "rb")
    assert summariser.summarise(image_file).get_value_tuple() == expected_colour.get_value_tuple()


@pytest.mark.parametrize(
    "filename,expected_colour",
    (
        ("test-sample-black.png", sRGBColor(0.14270557131030093, 0.14270557131030093, 0.1427060833145608)),
        ("test-sample-grey.png", sRGBColor(0.22093655922074024, 0.2757350121456547, 0.34224274333210736)),
        ("test-sample-navy.png", sRGBColor(0.003772143362497394, 0.003772143362497394, 0.31481252651473995)),
        ("test-sample-teal.png", sRGBColor(0.003567483878899318, 0.3851464969619143, 0.4321292530986342)),
    ),
)
def test_kmeans_image_summariser_regression(filename: str, expected_colour: sRGBColor) -> None:
    summariser = KMeansImageColourSummariser()
    image_file = open(settings.BASE_DIR / "images" / filename, "rb")
    # we allow some tolerance in the kmeans summariser because it involves randomness
    expected_red, expected_green, expected_blue = expected_colour.get_value_tuple()
    actual_red, actual_green, actual_blue = summariser.summarise(image_file).get_value_tuple()
    tolerance = 0.01
    for actual, expected in [
        (actual_red, expected_red),
        (actual_green, expected_green),
        (actual_blue, expected_blue),
    ]:
        assert abs(actual - expected) < tolerance
