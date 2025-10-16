import argparse
import importlib
import importlib.util
import os
from typing import Iterator, Optional

from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session, create_engine

_dotenv_spec = importlib.util.find_spec("dotenv")
if _dotenv_spec is not None:
    load_dotenv = importlib.import_module("dotenv").load_dotenv  # type: ignore[attr-defined]
else:
    def load_dotenv() -> bool:
        return False

load_dotenv()


def _build_url_from_components() -> Optional[str]:
    driver = os.getenv("DB_DRIVER", "mysql+pymysql")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    database = os.getenv("DB_NAME")
    port_raw = os.getenv("DB_PORT")

    if not all([username, password, host, database]):
        return None

    try:
        port = int(port_raw) if port_raw else None
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be an integer when provided") from exc

    url = URL.create(
        drivername=driver,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return url.render_as_string(hide_password=False)


def resolve_database_url() -> str:
    url = os.getenv("DB_URL") or _build_url_from_components()

    if not url:
        raise RuntimeError(
            "Database configuration missing. Provide DB_URL or the DB_* components in the environment."
        )

    return url


def _dialect_prefix(url: str) -> str:
    return url.split(":", 1)[0]


def _create_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}

    engine_kwargs = {"pool_pre_ping": True}
    if _dialect_prefix(url).startswith("mysql"):
        engine_kwargs["pool_recycle"] = 3600

    return create_engine(url, connect_args=connect_args, **engine_kwargs)


DB_URL = resolve_database_url()
engine = _create_engine(DB_URL)


def init_db() -> None:
    """Create all database tables defined on the metadata."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Yield a database session that is cleaned up automatically."""

    with Session(engine) as session:
        yield session


def verify_connection(url: Optional[str] = None) -> None:
    """Ensure the application can connect to the configured database."""

    target_engine = _create_engine(url) if url else engine
    try:
        with target_engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except SQLAlchemyError as exc:  # pragma: no cover - handled for runtime checks
        raise RuntimeError("Database connection test failed") from exc
    finally:
        if url:
            target_engine.dispose()


def _main() -> None:
    parser = argparse.ArgumentParser(description="Database utilities")
    parser.add_argument(
        "--check-connection",
        action="store_true",
        help="Verify the configured database is reachable",
    )
    parser.add_argument(
        "--url",
        help="Optional database URL to verify instead of the environment configuration",
    )
    args = parser.parse_args()

    if args.check_connection:
        try:
            verify_connection(args.url)
        except RuntimeError as exc:
            print(exc)
            raise SystemExit(1) from exc
        else:
            print("Database connection successful.")


if __name__ == "__main__":  # pragma: no cover - CLI helper
    _main()
