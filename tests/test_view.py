import pytest
from django.conf import Settings
from django.contrib.auth.models import User
from requests_mock import Mocker
from rest_framework.test import APIRequestFactory, force_authenticate

from closest_colour.colours import SRGBKDTreeColourMatcher
from closest_colour.views import MatchColour

# Import conftest to make sure we have access to fixtures
from . import conftest  # noqa: F401
from .test_colours import TEST_COLOURS_SRGB

PATH = "/colours/match"


def test_view_unauthenticated() -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 403
    assert response.data == {"detail": "Authentication credentials were not provided."}


@pytest.mark.django_db
def test_view_no_url(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH)
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Please specify a 'url' query parameter"]}


@pytest.mark.django_db
def test_view_non_http_url(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=file:///etc/passwd")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Only http or https URLs are allowed"]}


@pytest.mark.django_db
def test_view_invalid_url(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=wharblgarbl")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Only http or https URLs are allowed"]}


@pytest.mark.django_db
def test_view_invalid_colour_space(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=http://example.com&colour_space=wharblgarbl")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Invalid colour space"]}


@pytest.mark.django_db
def test_view_invalid_max_distance(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=http://example.com&max_distance=wharblgarbl")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Invalid max distance"]}


@pytest.mark.django_db
def test_view_invalid_image_summariser(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=http://example.com&summariser=wharblgarbl")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Invalid image summariser"]}


@pytest.mark.django_db
def test_view_invalid_image(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=http://example.com")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Could not parse image"]}


@pytest.mark.django_db
def test_view_invalid_domain(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=http://slsdrlguoirdhg.sedroguirsdg")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Could not fetch the URL given, could not connect"]}


@pytest.mark.django_db
def test_view_404(admin_user: User) -> None:
    arf = APIRequestFactory()
    request = arf.get(PATH + "?url=http://example.com/ofruhesoifuhsefuh")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    assert response.status_code == 400
    assert response.data == {"errors": ["Could not fetch the URL given, status code was 404"]}


@pytest.mark.parametrize(
    "filename,expected_colour_name,expected_distance",
    (
        ("1x1black.png", "black", 0.0),
        ("1x1white.png", "white", 0.0),
        ("test-sample-black.png", "NOT_FOUND", 0.0),
        ("test-sample-grey.png", "NOT_FOUND", 0.0),
        ("test-sample-navy.png", "navy", 0.1774),
        ("test-sample-teal.png", "teal", 0.1262),
    ),
)
@pytest.mark.django_db
def test_view_samples(
    admin_user: User,
    settings: Settings,
    filename: str,
    expected_colour_name: str,
    expected_distance: float,
    requests_mock: Mocker,
) -> None:
    setattr(settings, "COLOURS", TEST_COLOURS_SRGB)
    setattr(settings, "COLOUR_MATCHERS", {"srgb": SRGBKDTreeColourMatcher(getattr(settings, "COLOURS"))})

    url = f"http://test-colour-matching.test/{filename}"
    requests_mock.get(url, content=open(getattr(settings, "BASE_DIR") / "images" / filename, "rb").read())

    arf = APIRequestFactory()
    request = arf.get(PATH + f"?url={url}")
    force_authenticate(request, admin_user)
    view = MatchColour.as_view()
    response = view(request)
    if expected_colour_name == "NOT_FOUND":
        assert response.status_code == 404
        assert response.data == {"errors": ["No colour found within 0.2 units"]}
    else:
        assert response.status_code == 200
        assert sorted(response.data.keys()) == ["colour", "distance"]
        assert response.data["colour"] == expected_colour_name
        tolerance = 0.05
        assert abs(response.data["distance"] - expected_distance) < tolerance
