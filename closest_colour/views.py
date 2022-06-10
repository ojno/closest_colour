import urllib.parse
from io import BytesIO
from typing import cast

from django.conf import settings
import requests
from rest_framework import status, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class MatchColour(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        errors = []

        if "url" in request.query_params:
            url = request.query_params["url"]
            if not isinstance(url, str):
                errors.append("Please specify only one 'url' query parameter")
            url = cast(str, url)

            parsed_url = urllib.parse.urlparse(url)
            if parsed_url.scheme.lower() not in ("http", "https"):
                # prevent file:// attacks etc
                errors.append("Only http or https URLs are allowed")
        else:
            url = ""  # for "might be referenced before assignment"
            errors.append("Please specify a 'url' query parameter")

        space = request.query_params.get("colour_space", settings.DEFAULT_COLOUR_SPACE).lower()
        if space not in settings.COLOUR_MATCHERS or space not in settings.DEFAULT_MAX_DISTANCES:
            errors.append("Invalid colour space")

        max_distance_str = request.query_params.get("max_distance", None)
        if max_distance_str is None:
            max_distance = settings.DEFAULT_MAX_DISTANCES[space]
        else:
            try:
                max_distance = float(max_distance_str)
            except ValueError:
                max_distance = -1.0  # for "might be referenced before assignment"
                errors.append("Invalid max distance")

        summariser = request.query_params.get("summariser", settings.DEFAULT_IMAGE_SUMMARISER).lower()
        if summariser not in settings.IMAGE_SUMMARISERS:
            errors.append("Invalid image summariser")

        if errors != []:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # This is potentially a big security hole, at the very least for reflected DDOSes.
        # Make sure this view's permissions are set to at least IsAuthenticated.
        r = requests.get(url)
        if not r.ok:
            return Response(
                {"errors": [f"Could not fetch the URL given, status code was {r.status_code}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        image_file = BytesIO(r.content)

        image_colour = settings.IMAGE_SUMMARISERS[summariser].summarise(image_file)
        nearest_colour, distance = settings.COLOUR_MATCHERS[space].nearest(image_colour)

        if distance > max_distance:
            return Response(
                {"errors": [f"No colour found within {max_distance} units"]}, status=status.HTTP_404_NOT_FOUND
            )

        return Response({"colour": nearest_colour, "distance": distance})
