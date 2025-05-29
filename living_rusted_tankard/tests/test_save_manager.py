"""Test save manager functionality."""
import pytest
import tempfile
import json
import gzip
from pathlib import Path
from unittest.mock import Mock, patch

from tests.fixtures import clean_game_state
from tests.utils.test_helpers import temporary_directory

from core.persistence import SaveManager, SaveFormat, SaveMetadata


class TestSaveManager:
    """Test SaveManager core functionality."""
    
    def test_save_manager_initialization(self):
        """Test SaveManager initializes correctly."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            assert manager.save_dir.exists()
            assert manager.backup_dir.exists()
            assert manager.migrator is not None
            assert manager.validator is not None
    
    def test_save_game_json_format(self, clean_game_state):
        """Test saving game in JSON format."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Save game
            success = manager.save_game(
                clean_game_state,
                "test_save",
                "session_123",
                "TestPlayer",
                SaveFormat.JSON
            )
            
            assert success is True
            
            # Check files were created
            save_file = Path(temp_dir) / "test_save.save.json"
            meta_file = Path(temp_dir) / "test_save.save.json.meta"
            
            assert save_file.exists()
            assert meta_file.exists()
            
            # Verify save content
            with open(save_file, 'r') as f:
                save_data = json.load(f)
            
            assert "metadata" in save_data
            assert "game_state" in save_data
            assert save_data["metadata"]["version"] == manager.CURRENT_SAVE_VERSION
            assert save_data["metadata"]["player_name"] == "TestPlayer"
            assert save_data["game_state"] == clean_game_state
    
    def test_save_game_compressed_format(self, clean_game_state):
        """Test saving game in compressed format."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Save game
            success = manager.save_game(
                clean_game_state,
                "compressed_save",
                "session_456",
                "CompressedPlayer",
                SaveFormat.COMPRESSED_JSON
            )
            
            assert success is True
            
            # Check compressed file was created
            save_file = Path(temp_dir) / "compressed_save.save.json.gz"
            assert save_file.exists()
            
            # Verify compressed content can be read
            with gzip.open(save_file, 'rb') as f:
                json_data = f.read().decode('utf-8')
                save_data = json.loads(json_data)
            
            assert "metadata" in save_data
            assert "game_state" in save_data
            assert save_data["metadata"]["compressed"] is True
    
    def test_load_game_json_format(self, clean_game_state):
        """Test loading game from JSON format."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Save and then load
            manager.save_game(clean_game_state, "load_test", "session_789", "LoadPlayer")
            loaded_state = manager.load_game("load_test")
            
            assert loaded_state is not None
            assert loaded_state == clean_game_state
    
    def test_load_game_compressed_format(self, clean_game_state):
        """Test loading game from compressed format."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Save compressed and then load
            manager.save_game(
                clean_game_state, 
                "compressed_load_test", 
                "session_compressed", 
                "CompressedLoadPlayer",
                SaveFormat.COMPRESSED_JSON
            )
            loaded_state = manager.load_game("compressed_load_test")
            
            assert loaded_state is not None
            assert loaded_state == clean_game_state
    
    def test_load_nonexistent_save(self):
        """Test loading non-existent save returns None."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            loaded_state = manager.load_game("nonexistent_save")
            assert loaded_state is None
    
    def test_list_saves(self, clean_game_state):
        """Test listing available saves."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create multiple saves
            save_names = ["save1", "save2", "save3"]
            for name in save_names:
                manager.save_game(clean_game_state, name, f"session_{name}", f"Player_{name}")
            
            # List saves
            saves = manager.list_saves()
            
            assert len(saves) == 3
            save_names_found = {save["name"] for save in saves}
            assert save_names_found == set(save_names)
            
            # Check save info structure
            for save_info in saves:
                assert "name" in save_info
                assert "path" in save_info
                assert "size_bytes" in save_info
                assert "modified_at" in save_info
                assert "metadata" in save_info
    
    def test_delete_save(self, clean_game_state):
        """Test deleting saves."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create save
            manager.save_game(clean_game_state, "delete_test", "session_delete", "DeletePlayer")
            
            # Verify save exists
            saves_before = manager.list_saves()
            assert len(saves_before) == 1
            
            # Delete save
            success = manager.delete_save("delete_test")
            assert success is True
            
            # Verify save is gone
            saves_after = manager.list_saves()
            assert len(saves_after) == 0
    
    def test_delete_save_with_backup(self, clean_game_state):
        """Test deleting save creates backup."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create save
            manager.save_game(clean_game_state, "backup_delete_test", "session_backup", "BackupPlayer")
            
            # Delete with backup
            success = manager.delete_save("backup_delete_test", create_backup=True)
            assert success is True
            
            # Check backup was created
            backup_files = list(manager.backup_dir.glob("*backup_delete_test*"))
            assert len(backup_files) > 0
    
    def test_create_backup(self, clean_game_state):
        """Test creating backups manually."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create save
            manager.save_game(clean_game_state, "backup_test", "session_backup", "BackupTestPlayer")
            
            # Create backup
            success = manager.create_backup("backup_test", "manual_backup")
            assert success is True
            
            # Verify backup exists
            backup_files = list(manager.backup_dir.glob("*backup_test*manual_backup*"))
            assert len(backup_files) >= 1
    
    def test_restore_backup(self, clean_game_state):
        """Test restoring from backup."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create original save
            manager.save_game(clean_game_state, "restore_test", "session_restore", "RestorePlayer")
            
            # Create backup
            manager.create_backup("restore_test", "test_backup")
            
            # Delete original
            manager.delete_save("restore_test", create_backup=False)
            
            # Restore from backup
            success = manager.restore_backup("test_backup", "restore_test")
            assert success is True
            
            # Verify restored save works
            loaded_state = manager.load_game("restore_test")
            assert loaded_state is not None
            assert loaded_state == clean_game_state
    
    def test_save_validation_failure(self):
        """Test save fails when validation fails."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create invalid game state
            invalid_state = {"invalid": "data", "missing": "required_fields"}
            
            # Mock validator to fail
            with patch.object(manager.validator, 'validate_save_data') as mock_validate:
                mock_validate.return_value = Mock(is_valid=False, errors=["Invalid structure"])
                
                success = manager.save_game(invalid_state, "invalid_save", "session", "Player")
                assert success is False
    
    def test_save_overwrites_existing(self, clean_game_state):
        """Test saving overwrites existing files and creates backup."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create initial save
            manager.save_game(clean_game_state, "overwrite_test", "session1", "Player1")
            
            # Modify game state
            modified_state = clean_game_state.copy()
            modified_state["modified"] = True
            
            # Save again (should overwrite)
            success = manager.save_game(modified_state, "overwrite_test", "session2", "Player2")
            assert success is True
            
            # Load and verify it's the new version
            loaded_state = manager.load_game("overwrite_test")
            assert loaded_state["modified"] is True
            
            # Check backup was created
            backup_files = list(manager.backup_dir.glob("*overwrite_test*"))
            assert len(backup_files) >= 1


class TestSaveManagerMigration:
    """Test SaveManager migration functionality."""
    
    def test_load_with_migration(self, clean_game_state):
        """Test loading save that requires migration."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create save with old version
            old_save_data = {
                "metadata": {
                    "version": "0.9.0",  # Old version
                    "created_at": "2023-01-01T00:00:00",
                    "game_version": "0.9.0",
                    "format": "json",
                    "session_id": "old_session",
                    "player_name": "OldPlayer",
                    "checksum": "fake_checksum",
                    "size_bytes": 1000,
                    "compressed": False
                },
                "game_state": clean_game_state
            }
            
            # Write old save directly
            save_path = Path(temp_dir) / "old_save.save.json"
            with open(save_path, 'w') as f:
                json.dump(old_save_data, f)
            
            # Mock migration
            with patch.object(manager.migrator, 'migrate_save') as mock_migrate:
                migrated_data = old_save_data.copy()
                migrated_data["metadata"]["version"] = manager.CURRENT_SAVE_VERSION
                mock_migrate.return_value = migrated_data
                
                # Load save (should trigger migration)
                loaded_state = manager.load_game("old_save")
                
                assert loaded_state is not None
                mock_migrate.assert_called_once()
    
    def test_load_migration_failure(self, clean_game_state):
        """Test loading when migration fails."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create save with old version
            old_save_data = {
                "metadata": {
                    "version": "0.8.0",  # Very old version
                    "created_at": "2022-01-01T00:00:00",
                    "game_version": "0.8.0",
                    "format": "json",
                    "session_id": "very_old_session",
                    "player_name": "VeryOldPlayer",
                    "checksum": "fake_checksum",
                    "size_bytes": 1000,
                    "compressed": False
                },
                "game_state": clean_game_state
            }
            
            # Write old save
            save_path = Path(temp_dir) / "failed_migration.save.json"
            with open(save_path, 'w') as f:
                json.dump(old_save_data, f)
            
            # Mock migration failure
            with patch.object(manager.migrator, 'migrate_save') as mock_migrate:
                mock_migrate.return_value = None  # Migration failed
                
                # Load save (should fail gracefully)
                loaded_state = manager.load_game("failed_migration")
                
                assert loaded_state is None
                mock_migrate.assert_called_once()


class TestSaveManagerErrorHandling:
    """Test SaveManager error handling."""
    
    def test_save_disk_full_error(self, clean_game_state):
        """Test save handles disk full errors."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Mock disk full error
            with patch('builtins.open', side_effect=OSError("No space left on device")):
                success = manager.save_game(clean_game_state, "disk_full", "session", "Player")
                assert success is False
    
    def test_load_corrupted_file(self):
        """Test loading corrupted save file."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create corrupted save file
            save_path = Path(temp_dir) / "corrupted.save.json"
            with open(save_path, 'w') as f:
                f.write("{ corrupted json data")
            
            # Try to load corrupted save
            loaded_state = manager.load_game("corrupted")
            assert loaded_state is None
    
    def test_load_checksum_mismatch(self, clean_game_state):
        """Test loading save with checksum mismatch."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create save
            manager.save_game(clean_game_state, "checksum_test", "session", "Player")
            
            # Modify save file (corrupt it)
            save_path = Path(temp_dir) / "checksum_test.save.json"
            with open(save_path, 'r') as f:
                data = json.load(f)
            
            data["game_state"]["corrupted"] = True
            
            with open(save_path, 'w') as f:
                json.dump(data, f)
            
            # Try to load (should warn about checksum but still load)
            loaded_state = manager.load_game("checksum_test")
            
            # Should still load despite checksum mismatch
            assert loaded_state is not None
            assert loaded_state["corrupted"] is True
    
    def test_backup_creation_failure(self, clean_game_state):
        """Test backup creation failure handling."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Create save
            manager.save_game(clean_game_state, "backup_fail_test", "session", "Player")
            
            # Mock backup directory permission error
            with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
                success = manager.create_backup("backup_fail_test")
                assert success is False


class TestSaveMetadata:
    """Test SaveMetadata functionality."""
    
    def test_save_metadata_creation(self):
        """Test creating SaveMetadata objects."""
        metadata = SaveMetadata(
            version="1.0.0",
            created_at="2023-01-01T12:00:00",
            game_version="0.1.0",
            format=SaveFormat.JSON,
            checksum="abc123",
            size_bytes=1024,
            session_id="test_session",
            player_name="TestPlayer"
        )
        
        assert metadata.version == "1.0.0"
        assert metadata.format == SaveFormat.JSON
        assert metadata.size_bytes == 1024
        assert metadata.compressed is False  # Default value
    
    def test_save_metadata_serialization(self):
        """Test SaveMetadata to_dict and from_dict."""
        original = SaveMetadata(
            version="1.0.0",
            created_at="2023-01-01T12:00:00",
            game_version="0.1.0",
            format=SaveFormat.COMPRESSED_JSON,
            checksum="def456",
            size_bytes=2048,
            session_id="serialize_session",
            player_name="SerializePlayer",
            compressed=True
        )
        
        # Convert to dict
        metadata_dict = original.to_dict()
        
        assert isinstance(metadata_dict, dict)
        assert metadata_dict["version"] == "1.0.0"
        assert metadata_dict["compressed"] is True
        
        # Convert back from dict
        restored = SaveMetadata.from_dict(metadata_dict)
        
        assert restored.version == original.version
        assert restored.format == original.format
        assert restored.compressed == original.compressed
    
    def test_save_metadata_enum_handling(self):
        """Test SaveMetadata handles enum conversion."""
        # Test with string format (as would come from JSON)
        metadata_dict = {
            "version": "1.0.0",
            "created_at": "2023-01-01T12:00:00",
            "game_version": "0.1.0",
            "format": "json.gz",  # String instead of enum
            "checksum": "ghi789",
            "size_bytes": 4096,
            "session_id": "enum_session",
            "player_name": "EnumPlayer",
            "compressed": True
        }
        
        metadata = SaveMetadata.from_dict(metadata_dict)
        
        assert metadata.format == SaveFormat.COMPRESSED_JSON
        assert isinstance(metadata.format, SaveFormat)


class TestSaveManagerIntegration:
    """Test SaveManager integration scenarios."""
    
    def test_full_save_load_cycle(self, clean_game_state):
        """Test complete save/load cycle with all features."""
        with temporary_directory() as temp_dir:
            manager = SaveManager(temp_dir)
            
            # Modify game state to make it interesting
            game_state = clean_game_state.copy()
            game_state["player"]["gold"] = 500
            game_state["player"]["level"] = 5
            game_state["custom_data"] = {"test": "value"}
            
            # Save game
            save_success = manager.save_game(
                game_state,
                "full_cycle_test",
                "full_cycle_session",
                "FullCyclePlayer",
                SaveFormat.COMPRESSED_JSON
            )
            assert save_success is True
            
            # List saves
            saves = manager.list_saves()
            assert len(saves) == 1
            assert saves[0]["name"] == "full_cycle_test"
            
            # Load game
            loaded_state = manager.load_game("full_cycle_test")
            assert loaded_state is not None
            assert loaded_state == game_state
            
            # Create backup
            backup_success = manager.create_backup("full_cycle_test", "integration_test")
            assert backup_success is True
            
            # Delete original
            delete_success = manager.delete_save("full_cycle_test")
            assert delete_success is True
            
            # Restore from backup
            restore_success = manager.restore_backup("integration_test", "full_cycle_test")
            assert restore_success is True
            
            # Verify restoration
            final_loaded_state = manager.load_game("full_cycle_test")
            assert final_loaded_state == game_state