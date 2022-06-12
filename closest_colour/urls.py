from django.urls import path

from .views import MatchColour

urlpatterns = [
    path("match", MatchColour.as_view()),
]
