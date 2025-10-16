from collections.abc import Callable, Mapping
from typing import Iterator

import pytest
from fastapi import Request
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.main import app


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    try:
        yield engine
    finally:
        SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session(test_engine) -> Iterator[Session]:
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def request_factory() -> Callable[[str, Mapping[str, str] | None], Request]:
    def _factory(path: str, query: Mapping[str, str] | None = None) -> Request:
        query = query or {}
        query_items = [f"{key}={value}" for key, value in query.items()]
        query_string = "&".join(query_items).encode()
        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "query_string": query_string,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "app": app,
            "state": {},
        }
        return Request(scope)

    return _factory
