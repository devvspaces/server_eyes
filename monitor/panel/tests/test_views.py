import pytest

from django.urls import reverse


@pytest.mark.django_db
def test_view(client):
    url = reverse('panel:login')
    response = client.get(url)
    assert response.status_code == 200
