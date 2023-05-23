from django.conf import settings
import os
import hashlib


def get_setting(name: str) -> str | None:
    return getattr(settings, name, None) or os.getenv(name, None)


def hash_string(string):
    hash_object = hashlib.sha256()
    hash_object.update(string.encode("utf-8"))
    return hash_object.hexdigest()
