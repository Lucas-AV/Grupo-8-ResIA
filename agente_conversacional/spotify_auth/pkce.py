import base64
import hashlib
import secrets


def generate_code_verifier():
    return base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")


def generate_code_challenge(code_verifier):
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def generate_state():
    return secrets.token_urlsafe(24)
