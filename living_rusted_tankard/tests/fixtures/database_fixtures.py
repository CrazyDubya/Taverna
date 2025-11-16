"""Database-related test fixtures for isolation and testing."""
import pytest
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch
from contextlib import contextmanager
from typing import Generator

from core.db.session import DatabaseSession


@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def isolated_db_session(temp_database):
    """Create an isolated database session for testing."""

    class TestDatabaseSession:
        def __init__(self, db_path: str):
            self.db_path = db_path
            self.connection = None

        def __enter__(self):
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            return self.connection

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.connection:
                self.connection.close()

        def execute(self, query: str, params=None):
            with self as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.fetchall()

        def initialize_schema(self):
            """Initialize basic test schema."""
            schema_queries = [
                """CREATE TABLE IF NOT EXISTS game_state (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    gold INTEGER DEFAULT 100,
                    health INTEGER DEFAULT 100,
                    experience INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1
                )""",
                """CREATE TABLE IF NOT EXISTS npcs (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    personality TEXT,
                    location TEXT,
                    active BOOLEAN DEFAULT TRUE
                )""",
                """CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    player_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
            ]

            for query in schema_queries:
                self.execute(query)

    session = TestDatabaseSession(temp_database)
    session.initialize_schema()
    return session


@pytest.fixture
def mock_database_session():
    """Mock database session for unit tests that don't need real DB."""
    mock_session = Mock(spec=DatabaseSession)

    # Mock common database operations
    mock_session.save_game_state = Mock(return_value=True)
    mock_session.load_game_state = Mock(return_value=None)
    mock_session.get_player = Mock(return_value=None)
    mock_session.save_player = Mock(return_value=True)
    mock_session.get_npcs = Mock(return_value=[])
    mock_session.save_npc = Mock(return_value=True)

    return mock_session


@pytest.fixture
def database_transaction_manager(isolated_db_session):
    """Manage database transactions for tests."""

    class TransactionManager:
        def __init__(self, db_session):
            self.db_session = db_session
            self.savepoints = []

        @contextmanager
        def transaction(self):
            """Context manager for database transactions."""
            with self.db_session as conn:
                try:
                    conn.execute("BEGIN")
                    yield conn
                    conn.execute("COMMIT")
                except Exception:
                    conn.execute("ROLLBACK")
                    raise

        @contextmanager
        def savepoint(self, name: str):
            """Create a savepoint for nested transactions."""
            with self.db_session as conn:
                try:
                    conn.execute(f"SAVEPOINT {name}")
                    self.savepoints.append(name)
                    yield conn
                    conn.execute(f"RELEASE SAVEPOINT {name}")
                    self.savepoints.remove(name)
                except Exception:
                    conn.execute(f"ROLLBACK TO SAVEPOINT {name}")
                    if name in self.savepoints:
                        self.savepoints.remove(name)
                    raise

        def rollback_all(self):
            """Rollback all transactions and savepoints."""
            with self.db_session as conn:
                for savepoint in reversed(self.savepoints):
                    conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                conn.execute("ROLLBACK")
                self.savepoints.clear()

    return TransactionManager(isolated_db_session)


@pytest.fixture
def populated_test_database(isolated_db_session):
    """Create a database with test data."""
    # Insert test players
    test_players = [
        ("TestPlayer1", 100, 100, 0, 1),
        ("TestPlayer2", 500, 150, 250, 3),
        ("TestPlayer3", 50, 75, 100, 2),
    ]

    for name, gold, health, exp, level in test_players:
        isolated_db_session.execute(
            "INSERT INTO players (name, gold, health, experience, level) VALUES (?, ?, ?, ?, ?)",
            (name, gold, health, exp, level),
        )

    # Insert test NPCs
    test_npcs = [
        ("Barkeep Bob", "friendly", "tavern", True),
        ("Mysterious Stranger", "cryptic", "corner_table", True),
        ("Town Guard", "authoritative", "entrance", True),
    ]

    for name, personality, location, active in test_npcs:
        isolated_db_session.execute(
            "INSERT INTO npcs (name, personality, location, active) VALUES (?, ?, ?, ?)",
            (name, personality, location, active),
        )

    # Insert test sessions
    test_sessions = [("session_1", "TestPlayer1"), ("session_2", "TestPlayer2")]

    for session_id, player_name in test_sessions:
        isolated_db_session.execute(
            "INSERT INTO sessions (id, player_name) VALUES (?, ?)",
            (session_id, player_name),
        )

    return isolated_db_session


@pytest.fixture
def database_cleaner():
    """Utility for cleaning database state between tests."""

    class DatabaseCleaner:
        def __init__(self):
            self.tables_to_clean = ["game_state", "players", "npcs", "sessions"]

        def clean_all_tables(self, db_session):
            """Remove all data from test tables."""
            for table in self.tables_to_clean:
                try:
                    db_session.execute(f"DELETE FROM {table}")
                except Exception:
                    # Table might not exist, ignore
                    pass

        def clean_table(self, db_session, table_name: str):
            """Clean specific table."""
            db_session.execute(f"DELETE FROM {table_name}")

        def reset_sequences(self, db_session):
            """Reset auto-increment sequences."""
            for table in self.tables_to_clean:
                try:
                    db_session.execute(
                        f"DELETE FROM sqlite_sequence WHERE name='{table}'"
                    )
                except Exception:
                    # sqlite_sequence might not exist, ignore
                    pass

    return DatabaseCleaner()


@pytest.fixture(autouse=True)
def auto_database_cleanup(database_cleaner, isolated_db_session):
    """Automatically clean database after each test."""
    yield
    database_cleaner.clean_all_tables(isolated_db_session)
    database_cleaner.reset_sequences(isolated_db_session)
