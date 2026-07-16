from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.automation.models import Webhook, validate_webhook_target_url


def _resolves_to(*ips):
    return [(None, None, None, None, (ip, 0)) for ip in ips]


class TestWebhookSSRFValidation:
    def test_rejects_non_http_scheme(self):
        with pytest.raises(ValidationError):
            validate_webhook_target_url("file:///etc/passwd")

    @patch("apps.automation.models.socket.getaddrinfo")
    def test_rejects_loopback(self, mock_resolve):
        mock_resolve.return_value = _resolves_to("127.0.0.1")
        with pytest.raises(ValidationError):
            validate_webhook_target_url("http://localhost:8000/hook")

    @patch("apps.automation.models.socket.getaddrinfo")
    def test_rejects_cloud_metadata_link_local(self, mock_resolve):
        mock_resolve.return_value = _resolves_to("169.254.169.254")
        with pytest.raises(ValidationError):
            validate_webhook_target_url("http://metadata.internal/latest/meta-data/")

    @patch("apps.automation.models.socket.getaddrinfo")
    def test_rejects_private_range(self, mock_resolve):
        mock_resolve.return_value = _resolves_to("10.0.0.5")
        with pytest.raises(ValidationError):
            validate_webhook_target_url("http://internal-service/hook")

    @patch("apps.automation.models.socket.getaddrinfo")
    def test_allows_public_address(self, mock_resolve):
        mock_resolve.return_value = _resolves_to("93.184.216.34")
        validate_webhook_target_url("https://example.com/hook")  # should not raise

    @patch("apps.automation.models.socket.getaddrinfo")
    def test_rejects_if_any_resolved_address_is_private(self, mock_resolve):
        """DNS rebinding-style case: one public + one private A record."""
        mock_resolve.return_value = _resolves_to("93.184.216.34", "127.0.0.1")
        with pytest.raises(ValidationError):
            validate_webhook_target_url("http://rebinder.example.com/hook")


@pytest.mark.django_db
class TestWebhookModelValidation:
    @patch("apps.automation.models.socket.getaddrinfo")
    def test_full_clean_rejects_ssrf_target(self, mock_resolve):
        mock_resolve.return_value = _resolves_to("169.254.169.254")
        webhook = Webhook(
            name="evil", event="invoice.created",
            target_url="http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        )
        with pytest.raises(ValidationError):
            webhook.full_clean()

    @patch("apps.automation.models.socket.getaddrinfo")
    def test_deliver_blocks_ssrf_even_if_saved_without_full_clean(self, mock_resolve):
        mock_resolve.return_value = _resolves_to("127.0.0.1")
        webhook = Webhook.objects.create(
            name="bypass", event="invoice.created", target_url="http://127.0.0.1:9999/hook"
        )
        delivery = webhook.deliver({"x": 1})
        assert delivery.status == "failed"
        assert "non-public" in delivery.error or "resolve" in delivery.error.lower()


@pytest.mark.django_db
class TestWebhookAPIRejectsSSRF:
    @patch("apps.automation.models.socket.getaddrinfo")
    def test_api_create_rejects_ssrf_target(self, mock_resolve):
        from rest_framework.test import APIClient
        from apps.core.models import User

        mock_resolve.return_value = _resolves_to("169.254.169.254")
        user = User.objects.create_user(
            username="webhookuser", email="webhookuser@x.com", password="pw12345678"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        res = client.post(
            "/api/automation/webhooks/",
            {"name": "evil", "event": "invoice.created",
             "target_url": "http://169.254.169.254/latest/meta-data/"},
            format="json",
        )
        assert res.status_code == 400
