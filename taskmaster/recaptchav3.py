import os
import requests

try:
    from local_settings import RECAPTCHA_SITE_KEY, RECAPTCHA_SECRET_KEY
except ImportError:
    RECAPTCHA_SITE_KEY = None
    RECAPTCHA_SECRET_KEY = None

RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", RECAPTCHA_SITE_KEY)
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", RECAPTCHA_SECRET_KEY)


def verify_recaptcha(response_token, secret_key=None, remote_ip=None):
    """Verify a Google reCAPTCHA v3 token."""
    secret = secret_key or RECAPTCHA_SECRET_KEY
    if not response_token:
        return {"success": False, "error-codes": ["missing-input-response"]}
    if not secret:
        return {"success": False, "error-codes": ["missing-input-secret"]}

    payload = {
        "secret": secret,
        "response": response_token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
