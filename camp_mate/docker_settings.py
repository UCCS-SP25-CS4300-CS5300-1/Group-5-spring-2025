import os
import secrets

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

SECRET_KEY = secrets.token_urlsafe(
    64
)  ## Should be imported or generated in a better secrets env
