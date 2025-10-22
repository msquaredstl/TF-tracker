from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, Mapping, Optional
from urllib.parse import urlencode

import django
import pytest
from sqlmodel import Session, SQLModel, create_engine
from starlette.requests import Request

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DJANGO_ROOT = ROOT / "django_site"
if str(DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(DJANGO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tftracker.settings")
django.setup()


@pytest.fixture
def session(tmp_path) -> Session:
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()

    engine.dispose()


@pytest.fixture
def request_factory() -> Callable[[str, Optional[Mapping[str, str]]], Request]:
    def factory(path: str, query_params: Optional[Mapping[str, str]] = None) -> Request:
        query_string = urlencode(query_params or {}, doseq=True).encode("utf-8")
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "method": "GET",
            "scheme": "http",
            "path": path,
            "query_string": query_string,
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }

        async def receive() -> dict[str, object]:
            return {"type": "http.request", "body": b"", "more_body": False}

        return Request(scope, receive)

    return factory
