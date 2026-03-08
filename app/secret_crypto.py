import base64
import hashlib
import os

from flask import current_app, has_app_context


_ENC_PREFIX = "enc::"


def _get_encryption_seed():
    if has_app_context():
        seed = (
            current_app.config.get("SETTINGS_ENCRYPTION_KEY")
            or os.getenv("SETTINGS_ENCRYPTION_KEY")
            or current_app.config.get("SECRET_KEY")
            or os.getenv("SECRET_KEY")
            or ""
        )
    else:
        seed = os.getenv("SETTINGS_ENCRYPTION_KEY") or os.getenv("SECRET_KEY") or ""
    return str(seed)


def _build_fernet():
    from cryptography.fernet import Fernet

    seed = _get_encryption_seed()
    if not seed:
        raise RuntimeError("No encryption seed configured (SETTINGS_ENCRYPTION_KEY or SECRET_KEY).")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret_value(value):
    value = (value or "").strip()
    if not value:
        return ""
    f = _build_fernet()
    token = f.encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{_ENC_PREFIX}{token}"


def decrypt_secret_value(value, default=""):
    value = (value or "").strip()
    if not value:
        return default
    if not value.startswith(_ENC_PREFIX):
        # Backward compatibility for old plain-text records.
        return value
    token = value[len(_ENC_PREFIX):]
    if not token:
        return default
    try:
        f = _build_fernet()
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return default

