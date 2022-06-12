import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
@pytest.fixture()
def admin_user() -> User:
    return User.objects.create_superuser("admin", "admin@example.com", "admin")
