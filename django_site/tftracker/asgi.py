"""ASGI config for the Transformers Django project."""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tftracker.settings")

application = get_asgi_application()
