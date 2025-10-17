"""WSGI config for the Transformers Django project."""
from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tftracker.settings")

application = get_wsgi_application()
