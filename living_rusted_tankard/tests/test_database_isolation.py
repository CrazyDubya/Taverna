"""Test database isolation functionality."""
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch

from tests.fixtures.database_fixtures import (
    temp_database,
    isolated_db_session,
    database_transaction_manager,
    populated_test_database,
    database_cleaner,
)
from tests.utils.assertion_helpers import assert_session_valid


class TestDatabaseIsolation:
    """Test database isolation between test runs."""

    def test_temp_database_creation(self, temp_database):
        """Test that temporary database is created and cleaned up."""
        assert os.path.exists(temp_database)

        # Verify it's a valid SQLite database
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()
        conn.close()

        assert version is not None

    def test_isolated_session_schema_initialization(self, isolated_db_session):
        """Test that isolated database session has proper schema."""
        # Check that required tables exist
        result = isolated_db_session.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )

        table_names = [row[0] for row in result]
        expected_tables = ["game_state", "players", "npcs", "sessions"]

        for table in expected_tables:
            assert table in table_names, f"Table {table} not found in schema"

    def test_database_transaction_manager(self, database_transaction_manager):
        """Test transaction management functionality."""
        # Test successful transaction
        with database_transaction_manager.transaction() as conn:
            conn.execute(
                "INSERT INTO players (name, gold) VALUES (?, ?)",
                ("TransactionTest", 200),
            )

        # Verify data was committed
        result = database_transaction_manager.db_session.execute(
            "SELECT gold FROM players WHERE name = ?", ("TransactionTest",)
        )
        assert len(result) == 1
        assert result[0][0] == 200

    def test_database_transaction_rollback(self, database_transaction_manager):
        """Test transaction rollback on error."""
        try:
            with database_transaction_manager.transaction() as conn:
                conn.execute(
                    "INSERT INTO players (name, gold) VALUES (?, ?)",
                    ("RollbackTest", 300),
                )
                # Force an error
                raise Exception("Test error")
        except Exception:
            pass  # Expected

        # Verify data was rolled back
        result = database_transaction_manager.db_session.execute(
            "SELECT * FROM players WHERE name = ?", ("RollbackTest",)
        )
        assert len(result) == 0

    def test_database_savepoints(self, database_transaction_manager):
        """Test savepoint functionality for nested transactions."""
        with database_transaction_manager.transaction() as conn:
            conn.execute(
                "INSERT INTO players (name, gold) VALUES (?, ?)",
                ("SavepointTest1", 100),
            )

            try:
                with database_transaction_manager.savepoint("test_savepoint") as conn:
                    conn.execute(
                        "INSERT INTO players (name, gold) VALUES (?, ?)",
                        ("SavepointTest2", 200),
                    )
                    # Force savepoint rollback
                    raise Exception("Savepoint error")
            except Exception:
                pass  # Expected

            # First insert should still be there, second should be rolled back
            result = database_transaction_manager.db_session.execute(
                "SELECT name FROM players WHERE name LIKE 'SavepointTest%'"
            )
            names = [row[0] for row in result]
            assert "SavepointTest1" in names
            assert "SavepointTest2" not in names

    def test_populated_database_content(self, populated_test_database):
        """Test that populated database has expected test data."""
        # Check players
        players = populated_test_database.execute("SELECT name, gold FROM players")
        player_names = [row[0] for row in players]
        assert "TestPlayer1" in player_names
        assert "TestPlayer2" in player_names
        assert "TestPlayer3" in player_names

        # Check NPCs
        npcs = populated_test_database.execute("SELECT name FROM npcs")
        npc_names = [row[0] for row in npcs]
        assert "Barkeep Bob" in npc_names
        assert "Mysterious Stranger" in npc_names
        assert "Town Guard" in npc_names

        # Check sessions
        sessions = populated_test_database.execute(
            "SELECT id, player_name FROM sessions"
        )
        assert len(sessions) >= 2

    def test_database_cleaner_functionality(
        self, isolated_db_session, database_cleaner
    ):
        """Test database cleaning between tests."""
        # Add some test data
        isolated_db_session.execute(
            "INSERT INTO players (name, gold) VALUES (?, ?)", ("CleanerTest", 500)
        )
        isolated_db_session.execute(
            "INSERT INTO npcs (name, personality, location) VALUES (?, ?, ?)",
            ("CleanerNPC", "test", "test_location"),
        )

        # Verify data exists
        players = isolated_db_session.execute(
            "SELECT * FROM players WHERE name = 'CleanerTest'"
        )
        npcs = isolated_db_session.execute(
            "SELECT * FROM npcs WHERE name = 'CleanerNPC'"
        )
        assert len(players) == 1
        assert len(npcs) == 1

        # Clean database
        database_cleaner.clean_all_tables(isolated_db_session)

        # Verify data is cleaned
        players = isolated_db_session.execute(
            "SELECT * FROM players WHERE name = 'CleanerTest'"
        )
        npcs = isolated_db_session.execute(
            "SELECT * FROM npcs WHERE name = 'CleanerNPC'"
        )
        assert len(players) == 0
        assert len(npcs) == 0

    def test_database_sequence_reset(self, isolated_db_session, database_cleaner):
        """Test that auto-increment sequences are reset."""
        # Insert and delete data to increment sequences
        isolated_db_session.execute(
            "INSERT INTO players (name, gold) VALUES (?, ?)", ("SequenceTest1", 100)
        )
        isolated_db_session.execute(
            "INSERT INTO players (name, gold) VALUES (?, ?)", ("SequenceTest2", 200)
        )

        # Clean and reset sequences
        database_cleaner.clean_all_tables(isolated_db_session)
        database_cleaner.reset_sequences(isolated_db_session)

        # Insert new data and check ID starts from 1
        isolated_db_session.execute(
            "INSERT INTO players (name, gold) VALUES (?, ?)", ("NewSequenceTest", 300)
        )

        result = isolated_db_session.execute(
            "SELECT id FROM players WHERE name = 'NewSequenceTest'"
        )
        assert result[0][0] == 1  # Should start from 1 again

    def test_concurrent_database_access(self, temp_database):
        """Test that multiple database connections can be used concurrently."""
        import threading
        import time

        results = []
        errors = []

        def worker(worker_id):
            try:
                conn = sqlite3.connect(temp_database)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS concurrent_test (
                        id INTEGER PRIMARY KEY,
                        worker_id INTEGER,
                        timestamp REAL
                    )
                """
                )

                for i in range(5):
                    conn.execute(
                        "INSERT INTO concurrent_test (worker_id, timestamp) VALUES (?, ?)",
                        (worker_id, time.time()),
                    )
                    time.sleep(0.1)

                conn.commit()
                conn.close()
                results.append(f"Worker {worker_id} completed")
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")

        # Start multiple workers
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 3

        # Verify data integrity
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM concurrent_test")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 15  # 3 workers * 5 inserts each


class TestDatabaseSessionManagement:
    """Test database session lifecycle management."""

    def test_session_context_manager(self, isolated_db_session):
        """Test database session context manager behavior."""
        # Test successful context
        with isolated_db_session as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_session_execute_method(self, isolated_db_session):
        """Test convenient execute method."""
        # Test with parameters
        result = isolated_db_session.execute(
            "INSERT INTO players (name, gold) VALUES (?, ?)", ("ExecuteTest", 150)
        )

        # Test without parameters
        result = isolated_db_session.execute(
            "SELECT name, gold FROM players WHERE name = 'ExecuteTest'"
        )

        assert len(result) == 1
        assert result[0][0] == "ExecuteTest"
        assert result[0][1] == 150

    def test_session_error_handling(self, isolated_db_session):
        """Test database session error handling."""
        # Test invalid SQL
        with pytest.raises(Exception):
            isolated_db_session.execute("INVALID SQL STATEMENT")

        # Test constraint violation
        isolated_db_session.execute(
            "INSERT INTO players (name, gold) VALUES (?, ?)", ("UniqueTest", 100)
        )

        with pytest.raises(Exception):
            # Try to insert duplicate name
            isolated_db_session.execute(
                "INSERT INTO players (name, gold) VALUES (?, ?)", ("UniqueTest", 200)
            )


class TestDatabaseFixtureIntegration:
    """Test integration between different database fixtures."""

    def test_fixture_combination(
        self, populated_test_database, database_transaction_manager
    ):
        """Test using multiple database fixtures together."""
        # populated_test_database should work with transaction_manager
        with database_transaction_manager.transaction() as conn:
            conn.execute(
                "UPDATE players SET gold = gold + 100 WHERE name = 'TestPlayer1'"
            )

        # Verify update was committed
        result = populated_test_database.execute(
            "SELECT gold FROM players WHERE name = 'TestPlayer1'"
        )
        # Original gold was 100, should now be 200
        assert result[0][0] == 200

    def test_auto_cleanup_functionality(self, isolated_db_session):
        """Test that auto cleanup works between tests."""
        # This test relies on the auto_database_cleanup fixture
        # Add some data
        isolated_db_session.execute(
            "INSERT INTO players (name, gold) VALUES (?, ?)", ("AutoCleanTest", 999)
        )

        # Verify data exists
        result = isolated_db_session.execute(
            "SELECT * FROM players WHERE name = 'AutoCleanTest'"
        )
        assert len(result) == 1

        # The cleanup should happen automatically after this test

    def test_data_isolation_between_tests(self, isolated_db_session):
        """Test that data from previous test was cleaned up."""
        # This test should not see data from previous test
        result = isolated_db_session.execute(
            "SELECT * FROM players WHERE name = 'AutoCleanTest'"
        )
        assert len(result) == 0  # Should be clean due to auto cleanup
