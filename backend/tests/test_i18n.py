"""Comprehensive Pytest tests for i18n APIs."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.i18n.models import Language, Translation


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="test@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def english_lang():
    return Language.objects.create(
        code="en",
        name="English",
        name_local="English",
        direction="ltr",
        is_default=True,
    )


@pytest.fixture
def arabic_lang():
    return Language.objects.create(
        code="ar",
        name="Arabic",
        name_local="العربية",
        direction="rtl",
        is_default=False,
    )


@pytest.mark.django_db
class TestLanguageAPI:
    def test_list_languages(self, auth_client, english_lang, arabic_lang):
        response = auth_client.get("/api/i18n/languages/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_create_language(self, auth_client):
        data = {
            "code": "fr",
            "name": "French",
            "name_local": "Français",
            "direction": "ltr",
            "flag_emoji": "🇫🇷",
        }
        response = auth_client.post("/api/i18n/languages/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["code"] == "fr"

    def test_retrieve_language(self, auth_client, english_lang):
        response = auth_client.get(f"/api/i18n/languages/{english_lang.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == "en"

    def test_update_language(self, auth_client, english_lang):
        data = {"flag_emoji": "🇺🇸"}
        response = auth_client.patch(f"/api/i18n/languages/{english_lang.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        english_lang.refresh_from_db()
        assert english_lang.flag_emoji == "🇺🇸"

    def test_delete_language(self, auth_client, english_lang):
        response = auth_client.delete(f"/api/i18n/languages/{english_lang.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_default_action(self, auth_client, english_lang):
        response = auth_client.get("/api/i18n/languages/default/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == "en"

    def test_active_action(self, auth_client, english_lang, arabic_lang):
        arabic_lang.is_active = False
        arabic_lang.save()
        response = auth_client.get("/api/i18n/languages/active/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["code"] == "en"

    def test_unauthenticated_access(self, api_client):
        response = api_client.get("/api/i18n/languages/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTranslationAPI:
    def test_list_translations(self, auth_client, english_lang):
        Translation.objects.create(language=english_lang, key="hello", value="Hello", context="general")
        response = auth_client.get("/api/i18n/translations/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_translation(self, auth_client, english_lang):
        data = {
            "language": str(english_lang.id),
            "key": "welcome",
            "value": "Welcome to Nexus",
            "context": "auth",
        }
        response = auth_client.post("/api/i18n/translations/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["key"] == "welcome"

    def test_search_translations(self, auth_client, english_lang, arabic_lang):
        Translation.objects.create(language=english_lang, key="hello", value="Hello", context="general")
        Translation.objects.create(language=arabic_lang, key="hello", value="مرحبا", context="general")
        response = auth_client.get("/api/i18n/translations/search/?q=hello")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_filter_by_context(self, auth_client, english_lang):
        Translation.objects.create(language=english_lang, key="save", value="Save", context="actions")
        Translation.objects.create(language=english_lang, key="dashboard", value="Dashboard", context="navigation")
        response = auth_client.get("/api/i18n/translations/?context=actions")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_bulk_create(self, auth_client, english_lang):
        data = {
            "language_code": "en",
            "translations": [
                {"key": "new_key_1", "value": "Value 1", "context": "test"},
                {"key": "new_key_2", "value": "Value 2", "context": "test"},
            ],
        }
        response = auth_client.post("/api/i18n/translations/bulk/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["created"] == 2

    def test_bulk_update_existing(self, auth_client, english_lang):
        Translation.objects.create(language=english_lang, key="existing", value="Old", context="test")
        data = {
            "language_code": "en",
            "translations": [
                {"key": "existing", "value": "New", "context": "test"},
            ],
        }
        response = auth_client.post("/api/i18n/translations/bulk/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["updated"] == 1


@pytest.mark.django_db
class TestTranslationImportJobAPI:
    def test_list_import_jobs(self, auth_client):
        response = auth_client.get("/api/i18n/import-jobs/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_import_job(self, auth_client, english_lang):
        # Note: actual file upload requires multipart form data
        data = {
            "name": "Test Import",
            "language": str(english_lang.id),
        }
        response = auth_client.post("/api/i18n/import-jobs/", data)
        # May fail without file, but endpoint should be accessible
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]


@pytest.mark.django_db
class TestSeedCommand:
    def test_seed_i18n_command(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("seed_i18n", stdout=out)
        output = out.getvalue()
        assert "Seeded" in output
        assert Language.objects.filter(code="en").exists()
        assert Language.objects.filter(code="ar").exists()
        assert Translation.objects.count() > 0
