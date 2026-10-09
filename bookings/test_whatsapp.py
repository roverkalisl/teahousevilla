import datetime
import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from bookings.models import BookingInquiry, BookingNotification
from bookings.whatsapp import WhatsAppProvider, normalize_phone


class WhatsAppProviderTests(SimpleTestCase):
    def _success_response(self, body=b'{"messages":[{"id":"wamid.test"}]}'):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = body
        return response

    @patch("bookings.whatsapp.request.urlopen")
    def test_text_request_uses_bearer_token_versioned_url_and_normalized_recipient(self, urlopen):
        urlopen.return_value = self._success_response()
        provider = WhatsAppProvider(
            api_url="https://graph.facebook.com/v26.0/",
            access_token="test-access-token",
            phone_number_id="123456789",
        )

        sent, response_body, sent_at = provider.send_text("077 123 4567", "Test body")

        self.assertTrue(sent)
        self.assertIn("wamid.test", response_body)
        self.assertIsNotNone(sent_at)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://graph.facebook.com/v26.0/123456789/messages")
        self.assertEqual(request.headers["Authorization"], "Bearer test-access-token")
        self.assertEqual(request.headers["Content-type"], "application/json")
        self.assertEqual(json.loads(request.data), {
            "messaging_product": "whatsapp",
            "to": "94771234567",
            "type": "text",
            "text": {"body": "Test body"},
        })
        self.assertEqual(normalize_phone("+94 77 123 4567"), "94771234567")
        self.assertEqual(normalize_phone("0094 77 123 4567"), "94771234567")

    @patch("bookings.whatsapp.request.urlopen")
    def test_template_request_uses_template_payload_without_free_form_text(self, urlopen):
        urlopen.return_value = self._success_response()
        provider = WhatsAppProvider(
            api_url="https://graph.facebook.com/v26.0",
            access_token="test-access-token",
            phone_number_id="123456789",
        )

        sent, _, _ = provider.send_template(
            "0771234567",
            name="booking_confirmed",
            language="en",
            parameters=["Guest", "THV-202610-001", "01 October 2026", "04 October 2026", 2],
        )

        self.assertTrue(sent)
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["type"], "template")
        self.assertEqual(payload["template"]["name"], "booking_confirmed")
        self.assertEqual(payload["template"]["language"], {"code": "en"})
        self.assertEqual(
            [item["text"] for item in payload["template"]["components"][0]["parameters"]],
            ["Guest", "THV-202610-001", "01 October 2026", "04 October 2026", "2"],
        )
        self.assertNotIn("text", payload)

    @patch("bookings.whatsapp.request.urlopen")
    def test_meta_error_code_message_and_details_are_preserved_redacted_and_hinted(self, urlopen):
        body = {
            "error": {
                "message": "Outside the customer-service window",
                "type": "OAuthException",
                "code": 131047,
                "error_subcode": 2,
                "error_data": {"details": "Use an approved template. test-access-token"},
                "fbtrace_id": "trace-id",
            }
        }
        urlopen.side_effect = HTTPError(
            "https://graph.facebook.com/v26.0/123456789/messages",
            400,
            "Bad Request",
            {},
            BytesIO(json.dumps(body).encode()),
        )
        provider = WhatsAppProvider(
            api_url="https://graph.facebook.com/v26.0",
            access_token="test-access-token",
            phone_number_id="123456789",
        )

        sent, provider_response, sent_at = provider.send_text("0771234567", "Test")

        self.assertFalse(sent)
        self.assertIsNone(sent_at)
        error_record = json.loads(provider_response)
        self.assertEqual(error_record["error"]["code"], 131047)
        self.assertEqual(error_record["error"]["message"], body["error"]["message"])
        self.assertEqual(
            error_record["error"]["error_data"]["details"],
            "Use an approved template. [REDACTED]",
        )
        self.assertEqual(error_record["error"]["fbtrace_id"], "trace-id")
        self.assertIn("24-hour customer-service window", error_record["user_message"])
        self.assertNotIn("test-access-token", provider_response)

    @patch("bookings.whatsapp.request.urlopen")
    def test_common_auth_and_template_errors_preserve_meta_fields(self, urlopen):
        provider = WhatsAppProvider(
            api_url="https://graph.facebook.com/v26.0",
            access_token="test-access-token",
            phone_number_id="123456789",
        )
        failures = [
            (190, "Invalid OAuth access token", "Token expired"),
            (132001, "Template name does not exist", "Check approved template name"),
        ]

        for code, message, details in failures:
            urlopen.side_effect = HTTPError(
                "https://graph.facebook.com/v26.0/123456789/messages",
                400,
                "Bad Request",
                {},
                BytesIO(json.dumps({
                    "error": {
                        "code": code,
                        "message": message,
                        "error_data": {"details": details},
                    }
                }).encode()),
            )

            with self.subTest(meta_code=code):
                sent, provider_response, _ = provider.send_text("0771234567", "Test")

                self.assertFalse(sent)
                stored_error = json.loads(provider_response)
                self.assertEqual(stored_error["error"]["code"], code)
                self.assertEqual(stored_error["error"]["message"], message)
                self.assertEqual(stored_error["error"]["error_data"]["details"], details)

    @patch("bookings.whatsapp.request.urlopen")
    def test_invalid_api_url_fails_before_network_request(self, urlopen):
        provider = WhatsAppProvider(
            api_url="https://graph.facebook.com/v20.0/123456789/messages",
            access_token="test-access-token",
            phone_number_id="123456789",
        )

        sent, error_message, sent_at = provider.send_text("0771234567", "Test")

        self.assertFalse(sent)
        self.assertIn("versioned Graph API root", error_message)
        self.assertIsNone(sent_at)
        urlopen.assert_not_called()

    @patch("bookings.whatsapp.request.urlopen")
    def test_booking_template_must_be_configured_and_approved_template_used(self, urlopen):
        provider = WhatsAppProvider(
            api_url="https://graph.facebook.com/v26.0",
            access_token="test-access-token",
            phone_number_id="123456789",
        )

        sent, error_response, _ = provider.send_template("0771234567", name="")

        self.assertFalse(sent)
        self.assertIn("approved WhatsApp template name is not configured", json.loads(error_response)["user_message"])
        urlopen.assert_not_called()


class WhatsAppAdminErrorTests(TestCase):
    def test_booking_detail_shows_safe_meta_error_summary(self):
        booking = BookingInquiry.objects.create(
            full_name="Guest",
            phone="94770000000",
            email="guest@example.com",
            check_in=datetime.date(2026, 12, 10),
            check_out=datetime.date(2026, 12, 13),
        )
        BookingNotification.objects.create(
            booking=booking,
            notification_type=BookingNotification.TYPE_CONFIRMED,
            recipient="94770000000",
            message="Booking confirmed",
            message_status=BookingNotification.STATUS_FAILED,
            provider_response=json.dumps({
                "http_status": 400,
                "user_message": "The 24-hour customer-service window has expired; use an approved template instead of free-form text.",
                "error": {
                    "code": 131047,
                    "message": "Outside the 24-hour window",
                    "error_data": {"details": "Submit an approved template"},
                },
            }),
        )
        user = get_user_model().objects.create_user(username="owner", password="test-password", is_staff=True)
        self.client.force_login(user)

        response = self.client.get(reverse("bookings:manage_detail", args=[booking.pk]))

        self.assertContains(response, "Meta error 131047")
        self.assertContains(response, "Outside the 24-hour window")
        self.assertContains(response, "Details: Submit an approved template")
        self.assertNotContains(response, "test-access-token")
