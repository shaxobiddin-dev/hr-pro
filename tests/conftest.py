"""
Pytest configuration and fixtures.
"""

import pytest
from django.test import Client


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(client, django_user_model):
    """Authenticated Django test client."""
    user = django_user_model.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )
    client.force_login(user)
    return client


@pytest.fixture
def user(django_user_model):
    """Create a test user."""
    return django_user_model.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def admin_user(django_user_model):
    """Create an admin user."""
    return django_user_model.objects.create_superuser(
        email='admin@example.com',
        username='admin',
        password='adminpass123'
    )
