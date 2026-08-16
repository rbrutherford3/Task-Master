import os
import requests

try:
    from local_settings import TURNSTILE_SECRET
except ImportError:
    TURNSTILE_SECRET = None

TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "0x4AAAAAAERyvc7m3VJMNDiK")
TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET", TURNSTILE_SECRET)
TURNSTILE_HOSTNAMES = {
    hostname.strip()
    for hostname in os.environ.get(
        "TURNSTILE_HOSTNAMES", "masteroftasks.com,localhost,127.0.0.1,testserver"
    ).split(",")
    if hostname.strip()
}


def verify_turnstile(response_token, expected_action, hostname, secret_key=None, remote_ip=None):
    """Verify a Turnstile token and its protected-surface metadata."""
    secret = secret_key or TURNSTILE_SECRET
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
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=payload,
        timeout=10,
    )
    response.raise_for_status()
    result = response.json()
    if (
        not result.get("success")
        or result.get("action") != expected_action
        or result.get("hostname") not in TURNSTILE_HOSTNAMES
        or result.get("hostname") != hostname
    ):
        result["success"] = False
    return result
