import os

from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured


def get_encryption_key():
    key = os.environ.get("DJANGO_AC_ENCRYPTION_KEY")

    if not key:
        raise ImproperlyConfigured(
            "DJANGO_AC_ENCRYPTION_KEY environment variable is not set."
        )

    try:
        return key.encode()
    except AttributeError:
        raise ImproperlyConfigured(
            "DJANGO_AC_ENCRYPTION_KEY is invalid."
        )


def encrypt_password(password):
    if not password:
        return ""

    fernet = Fernet(get_encryption_key())

    return fernet.encrypt(
        password.encode("utf-8")
    ).decode("utf-8")


def decrypt_password(encrypted_password):
    if not encrypted_password:
        return ""

    fernet = Fernet(get_encryption_key())

    return fernet.decrypt(
        encrypted_password.encode("utf-8")
    ).decode("utf-8")