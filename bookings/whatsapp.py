import json
import re
from urllib import error, request
from urllib.parse import urlsplit

from django.conf import settings
from django.utils import timezone

DEFAULT_COUNTRY_CODE = "94"
GRAPH_API_ROOT_PATTERN = re.compile(r"/v\d+\.\d+")


def normalize_phone(raw, country_code=DEFAULT_COUNTRY_CODE):
    """Convert Sri Lankan local or international numbers to digits-only format."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = country_code + digits[1:]
    elif len(digits) == 9 and digits.startswith("7"):
        digits = country_code + digits
    return digits


_HINTS = {
    10: "The access token is missing the whatsapp_business_messaging permission.",
    190: "The access token is invalid or expired.",
    100: "Check the phone number ID and recipient phone number format.",
    131026: "The recipient may not be a WhatsApp user or may not have accepted WhatsApp terms.",
    131030: "The recipient is not on the allowed list for this test number.",
    131047: "The 24-hour customer-service window has expired; use an approved template instead of free-form text.",
    132000: "The template parameter count does not match the approved template.",
    132001: "The template name or language is not approved for this WhatsApp Business Account.",
    133010: "The sender phone number is not registered or active on the WhatsApp Cloud API.",
}


def _local_error(message):
    return json.dumps({"error": {}, "user_message": message})


def _redact_token(value, token):
    if isinstance(value, str) and token:
        return value.replace(token, "[REDACTED]")
    if isinstance(value, list):
        return [_redact_token(item, token) for item in value]
    if isinstance(value, dict):
        return {key: _redact_token(item, token) for key, item in value.items()}
    return value


def _http_error_response(exc, access_token):
    """Keep Meta's error object intact while adding a safe, useful hint."""
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except (OSError, AttributeError):
        body = ""

    try:
        response_body = json.loads(body)
    except json.JSONDecodeError:
        response_body = {"response_body": body}

    response_body = _redact_token(response_body, access_token)
    api_error = response_body.get("error", {}) if isinstance(response_body, dict) else {}
    code = api_error.get("code") if isinstance(api_error, dict) else None
    response_body = {
        "http_status": exc.code,
        "error": api_error if isinstance(api_error, dict) else {},
        "meta_response": response_body,
        "user_message": _HINTS.get(code, "Meta rejected the WhatsApp request. Review the error details below."),
    }
    return json.dumps(response_body, ensure_ascii=False)


def _api_root_error(api_url):
    try:
        parsed = urlsplit(api_url)
        port = parsed.port
    except ValueError:
        return "WHATSAPP_API_URL is not a valid versioned Graph API root."
    path = parsed.path.rstrip("/")
    if (
        parsed.scheme != "https"
        or parsed.hostname != "graph.facebook.com"
        or port is not None
        or parsed.query
        or parsed.fragment
        or not GRAPH_API_ROOT_PATTERN.fullmatch(path)
    ):
        return (
            "WHATSAPP_API_URL must be the versioned Graph API root, "
            "for example https://graph.facebook.com/v26.0."
        )
    return ""


class WhatsAppProvider:
    """Small provider adapter so booking logic is independent of transport details."""

    def __init__(self, api_url=None, access_token=None, phone_number_id=None):
        self.api_url = (api_url if api_url is not None else getattr(settings, "WHATSAPP_API_URL", "")).strip()
        self.access_token = (access_token if access_token is not None else getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")).strip()
        self.phone_number_id = (phone_number_id if phone_number_id is not None else getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")).strip()

    def missing_config(self):
        return [name for name, value in (
            ("WHATSAPP_API_URL", self.api_url),
            ("WHATSAPP_ACCESS_TOKEN", self.access_token),
            ("WHATSAPP_PHONE_NUMBER_ID", self.phone_number_id),
        ) if not value]

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _post(self, body):
        missing = self.missing_config()
        if missing:
            return False, _local_error("WhatsApp provider is not configured. Missing: " + ", ".join(missing)), None
        config_error = _api_root_error(self.api_url)
        if config_error:
            return False, _local_error(config_error), None

        url = f"{self.api_url.rstrip('/')}/{self.phone_number_id}/messages"
        req = request.Request(url, data=json.dumps(body).encode(), headers=self._headers(), method="POST")
        try:
            with request.urlopen(req, timeout=15) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                return True, _redact_token(response_body, self.access_token), timezone.now()
        except error.HTTPError as exc:
            return False, _http_error_response(exc, self.access_token), None
        except (error.URLError, TimeoutError, ValueError) as exc:
            message = _redact_token(f"WhatsApp network error: {exc}", self.access_token)
            return False, _local_error(message), None

    def send_text(self, recipient, message):
        to = normalize_phone(recipient)
        if not to:
            return False, _local_error("Invalid recipient phone number."), None
        return self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        })

    def send_template(self, recipient, name="hello_world", language="en_US", parameters=None):
        to = normalize_phone(recipient)
        if not to:
            return False, _local_error("Invalid recipient phone number."), None
        missing = self.missing_config()
        if missing:
            return False, _local_error("WhatsApp provider is not configured. Missing: " + ", ".join(missing)), None
        config_error = _api_root_error(self.api_url)
        if config_error:
            return False, _local_error(config_error), None
        if not name:
            return False, _local_error("An approved WhatsApp template name is not configured."), None

        template = {"name": name, "language": {"code": language}}
        if parameters:
            template["components"] = [{
                "type": "body",
                "parameters": [{"type": "text", "text": str(value)} for value in parameters],
            }]
        return self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template,
        })

    def check_phone_number(self):
        """Query the sender phone number to verify token, ID and registration status."""
        missing = self.missing_config()
        if missing:
            return False, "Missing: " + ", ".join(missing)
        config_error = _api_root_error(self.api_url)
        if config_error:
            return False, config_error

        url = (
            f"{self.api_url.rstrip('/')}/{self.phone_number_id}"
            "?fields=display_phone_number,verified_name,quality_rating,code_verification_status,status"
        )
        req = request.Request(url, headers=self._headers())
        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8", errors="replace")
                return True, _redact_token(body, self.access_token)
        except error.HTTPError as exc:
            return False, _http_error_response(exc, self.access_token)
        except (error.URLError, TimeoutError, ValueError) as exc:
            return False, _redact_token(f"WhatsApp network error: {exc}", self.access_token)
