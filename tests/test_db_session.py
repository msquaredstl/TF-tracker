import os
from unittest import TestCase, mock

os.environ.setdefault("DB_URL", "sqlite:///./test.db")

import app.db.session as db_session
from sqlalchemy.exc import SQLAlchemyError


class VerifyConnectionTests(TestCase):
    def test_verify_connection_executes_select(self) -> None:
        mock_connection = mock.MagicMock()
        connection_cm = mock.MagicMock()
        connection_cm.__enter__.return_value = mock_connection
        connection_cm.__exit__.return_value = False

        with mock.patch.object(db_session.engine, "connect", return_value=connection_cm) as connect:
            db_session.verify_connection()

        connect.assert_called_once_with()
        mock_connection.exec_driver_sql.assert_called_once_with("SELECT 1")

    def test_verify_connection_raises_runtime_error_on_failure(self) -> None:
        with mock.patch.object(
            db_session.engine, "connect", side_effect=SQLAlchemyError("boom")
        ):
            with self.assertRaises(RuntimeError):
                db_session.verify_connection()

    def test_verify_connection_with_override_url_uses_temporary_engine(self) -> None:
        mock_connection = mock.MagicMock()
        connection_cm = mock.MagicMock()
        connection_cm.__enter__.return_value = mock_connection
        connection_cm.__exit__.return_value = False

        temp_engine = mock.MagicMock()
        temp_engine.connect.return_value = connection_cm

        override_url = "mysql+pymysql://u:p@h:3306/db"

        with mock.patch("app.db.session._create_engine", return_value=temp_engine) as create_engine:
            db_session.verify_connection(override_url)

        create_engine.assert_called_once_with(override_url)
        temp_engine.connect.assert_called_once_with()
        mock_connection.exec_driver_sql.assert_called_once_with("SELECT 1")
        temp_engine.dispose.assert_called_once_with()


class ResolveDatabaseURLTests(TestCase):
    def test_resolve_defaults_to_sqlite_when_unconfigured(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                db_session.resolve_database_url(),
                db_session.DEFAULT_SQLITE_URL,
            )

    def test_resolve_from_components(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "DB_DRIVER": "mysql+pymysql",
                "DB_HOST": "example.com",
                "DB_PORT": "3306",
                "DB_NAME": "sample",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
            },
            clear=True,
        ):
            self.assertEqual(
                db_session.resolve_database_url(),
                "mysql+pymysql://user:pass@example.com:3306/sample",
            )

    def test_resolve_requires_all_components_when_any_provided(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "DB_HOST": "example.com",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                db_session.resolve_database_url()

    def test_resolve_requires_integer_port(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "DB_DRIVER": "mysql+pymysql",
                "DB_HOST": "example.com",
                "DB_PORT": "not-a-number",
                "DB_NAME": "sample",
                "DB_USER": "user",
                "DB_PASSWORD": "pass",
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                db_session.resolve_database_url()
