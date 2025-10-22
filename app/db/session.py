import argparse
import importlib
import importlib.util
import os
from typing import Iterator, Optional, Sequence

from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine

_dotenv_spec = importlib.util.find_spec("dotenv")
if _dotenv_spec is not None:
    load_dotenv = importlib.import_module("dotenv").load_dotenv  # type: ignore[attr-defined]
else:

    def load_dotenv() -> bool:
        return False


load_dotenv()

DEFAULT_SQLITE_URL = "sqlite:///./collection.db"
_REQUIRED_COMPONENT_KEYS: Sequence[str] = (
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_NAME",
)


def _build_url_from_components() -> Optional[str]:
    required_values = {key: os.getenv(key) for key in _REQUIRED_COMPONENT_KEYS}
    provided_required = {key: value for key, value in required_values.items() if value}

    if provided_required and len(provided_required) != len(required_values):
        missing = ", ".join(
            sorted(key for key, value in required_values.items() if not value)
        )
        raise RuntimeError(
            "Incomplete component-based database configuration. Missing environment variables: "
            f"{missing}."
        )

    if not provided_required:
        return None

    driver = os.getenv("DB_DRIVER", "mysql+pymysql")
    port_raw = os.getenv("DB_PORT")

    try:
        port = int(port_raw) if port_raw else None
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be an integer when provided") from exc

    url = URL.create(
        drivername=driver,
        username=required_values["DB_USER"],
        password=required_values["DB_PASSWORD"],
        host=required_values["DB_HOST"],
        port=port,
        database=required_values["DB_NAME"],
    )
    return url.render_as_string(hide_password=False)


def resolve_database_url() -> str:
    url = os.getenv("DB_URL")
    if url:
        return url

    component_url = _build_url_from_components()
    if component_url:
        return component_url

    return DEFAULT_SQLITE_URL


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
