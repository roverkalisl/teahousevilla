import json
from urllib import error, request

from django.conf import settings
from django.utils import timezone


class WhatsAppProvider:
    """Small provider adapter so booking logic is independent of transport details."""

    def __init__(self, api_url=None, access_token=None, phone_number_id=None):
        self.api_url = api_url if api_url is not None else getattr(settings, "WHATSAPP_API_URL", "")
        self.access_token = access_token if access_token is not None else getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = phone_number_id if phone_number_id is not None else getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")

    def send_text(self, recipient, message):
        if not self.api_url or not self.access_token or not self.phone_number_id:
            return False, "WhatsApp provider is not configured.", None

        payload = json.dumps({
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message},
        }).encode()
        try:
            req = request.Request(
                f"{self.api_url.rstrip('/')}/{self.phone_number_id}/messages",
                data=payload,
                headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
            )
            with request.urlopen(req, timeout=15) as response:
                return True, response.read().decode(), timezone.now()
        except (error.HTTPError, error.URLError, TimeoutError, ValueError) as exc:
            return False, str(exc), None
