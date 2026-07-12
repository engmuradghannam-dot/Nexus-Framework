"""Minimal RFC-6238 TOTP (pure Python, no external deps)."""
import base64
import hashlib
import hmac
import os
import struct
import time


def random_base32(length=32):
    raw = os.urandom(length)
    return base64.b32encode(raw).decode("utf-8").rstrip("=")[:length]


def _hotp(secret_b32, counter, digits=6):
    padding = "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(secret_b32.upper() + padding)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


def now_totp(secret_b32, step=30, digits=6):
    return _hotp(secret_b32, int(time.time() // step), digits)


def verify(secret_b32, code, step=30, digits=6, window=1):
    if not code:
        return False
    code = str(code).strip()
    counter = int(time.time() // step)
    for drift in range(-window, window + 1):
        if _hotp(secret_b32, counter + drift, digits) == code:
            return True
    return False


def provisioning_uri(secret_b32, account_name, issuer="Nexus ERP"):
    from urllib.parse import quote
    label = quote(f"{issuer}:{account_name}")
    return (
        f"otpauth://totp/{label}?secret={secret_b32}"
        f"&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"
    )
