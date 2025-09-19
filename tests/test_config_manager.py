import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from pipeline.config_manager import ConfigManager, ConfigurationError
from models.config import PipelineConfig


class TestConfigManager:
    @pytest.fixture
    def valid_config_dict(self):
        return {
            "hasura_endpoint": "https://test.hasura.app/v1/graphql",
            "materialized_views": ["curriculum_units", "curriculum_lessons"],
            "node_mappings": [
                {
                    "label": "Unit",
                    "id_field": "unit_id",
                    "properties": {
                        "id": {"source_field": "unit_id", "target_type": "string"},
                        "title": {
                            "source_field": "unit_title",
                            "target_type": "string",
                        },
                    },
                }
            ],
            "relationship_mappings": [
                {
                    "type": "CONTAINS",
                    "start_node_id_field": "unit_id",
                    "end_node_id_field": "lesson_id",
                    "properties": {
                        "order": {"source_field": "order_in_unit", "target_type": "int"}
                    },
                }
            ],
        }

    @pytest.fixture
    def temp_config_dir(self, valid_config_dict):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            with open(config_path, "w") as f:
                json.dump(valid_config_dict, f)
            yield temp_dir

    def test_init_with_existing_directory(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)
        assert manager.config_dir == Path(temp_config_dir)

    def test_init_with_nonexistent_directory(self):
        with pytest.raises(
            ConfigurationError, match="Configuration directory.*does not exist"
        ):
            ConfigManager("/nonexistent/directory")

    def test_load_valid_config(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)
        config = manager.load_config("test_config.json")

        assert isinstance(config, PipelineConfig)
        assert config.hasura_endpoint == "https://test.hasura.app/v1/graphql"
        assert len(config.materialized_views) == 2
        assert len(config.node_mappings) == 1
        assert len(config.relationship_mappings) == 1

    def test_load_nonexistent_config(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        with pytest.raises(
            ConfigurationError, match="Configuration file.*does not exist"
        ):
            manager.load_config("nonexistent.json")

    def test_load_invalid_json(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        # Create invalid JSON file
        invalid_path = Path(temp_config_dir) / "invalid.json"
        with open(invalid_path, "w") as f:
            f.write("{ invalid json")

        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            manager.load_config("invalid.json")

    def test_load_config_validation_error(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        # Create config with missing required field
        invalid_config = {"materialized_views": ["test"]}  # Missing hasura_endpoint
        invalid_path = Path(temp_config_dir) / "invalid_config.json"
        with open(invalid_path, "w") as f:
            json.dump(invalid_config, f)

        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            manager.load_config("invalid_config.json")

    def test_environment_variable_substitution(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        # Create config with environment variable placeholders
        config_with_env = {
            "hasura_endpoint": "${HASURA_ENDPOINT}",
            "materialized_views": ["test"],
            "node_mappings": [],
            "relationship_mappings": [],
        }
        env_config_path = Path(temp_config_dir) / "env_config.json"
        with open(env_config_path, "w") as f:
            json.dump(config_with_env, f)

        # Mock environment variable
        with patch.dict(
            os.environ, {"HASURA_ENDPOINT": "https://env.hasura.app/v1/graphql"}
        ):
            config = manager.load_config("env_config.json")
            assert config.hasura_endpoint == "https://env.hasura.app/v1/graphql"

    def test_environment_variable_substitution_missing(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        # Create config with environment variable that doesn't exist
        config_with_missing_env = {
            "hasura_endpoint": "${MISSING_VAR}",
            "materialized_views": ["test"],
            "node_mappings": [],
            "relationship_mappings": [],
        }
        missing_env_path = Path(temp_config_dir) / "missing_env.json"
        with open(missing_env_path, "w") as f:
            json.dump(config_with_missing_env, f)

        # Should raise ConfigurationError for missing env var
        with pytest.raises(
            ConfigurationError, match="Environment variable MISSING_VAR is not set"
        ):
            manager.load_config("missing_env.json")

    def test_nested_environment_variable_substitution(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        # Create config with nested env vars
        nested_config = {
            "hasura_endpoint": "https://test.com/v1/graphql",
            "materialized_views": ["test"],
            "node_mappings": [
                {
                    "label": "${NODE_LABEL}",
                    "id_field": "id",
                    "properties": {
                        "name": {
                            "source_field": "${SOURCE_FIELD}",
                            "target_type": "string",
                        }
                    },
                }
            ],
            "relationship_mappings": [],
        }
        nested_path = Path(temp_config_dir) / "nested_config.json"
        with open(nested_path, "w") as f:
            json.dump(nested_config, f)

        with patch.dict(
            os.environ, {"NODE_LABEL": "TestNode", "SOURCE_FIELD": "test_field"}
        ):
            config = manager.load_config("nested_config.json")
            assert config.node_mappings[0].label == "TestNode"
            assert (
                config.node_mappings[0].properties["name"].source_field == "test_field"
            )

    def test_file_read_permission_error(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        config_path = Path(temp_config_dir) / "permission_test.json"
        with open(config_path, "w") as f:
            json.dump({"test": "data"}, f)

        # Make file unreadable
        os.chmod(config_path, 0o000)

        try:
            with pytest.raises(ConfigurationError, match="Failed to read"):
                manager.load_config("permission_test.json")
        finally:
            # Restore permissions for cleanup
            os.chmod(config_path, 0o644)

    def test_complex_valid_configuration(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        # Create a complex but valid configuration
        complex_config = {
            "hasura_endpoint": "https://complex.hasura.app/v1/graphql",
            "materialized_views": [
                "curriculum_units",
                "curriculum_lessons",
                "lesson_relationships",
            ],
            "test_limit": 100,
            "node_mappings": [
                {
                    "label": "Unit",
                    "id_field": "unit_id",
                    "properties": {
                        "id": {"source_field": "unit_id", "target_type": "string"},
                        "title": {
                            "source_field": "unit_title",
                            "target_type": "string",
                            "transformation": "strip",
                        },
                        "stage": {"source_field": "key_stage", "target_type": "int"},
                    },
                },
                {
                    "label": "Lesson",
                    "id_field": "lesson_id",
                    "properties": {
                        "id": {"source_field": "lesson_id", "target_type": "string"},
                        "title": {
                            "source_field": "lesson_title",
                            "target_type": "string",
                            "transformation": "uppercase",
                        },
                    },
                },
            ],
            "relationship_mappings": [
                {
                    "type": "CONTAINS",
                    "start_node_id_field": "unit_id",
                    "end_node_id_field": "lesson_id",
                    "properties": {
                        "order": {"source_field": "order_in_unit", "target_type": "int"}
                    },
                }
            ],
        }

        complex_path = Path(temp_config_dir) / "complex_config.json"
        with open(complex_path, "w") as f:
            json.dump(complex_config, f)

        config = manager.load_config("complex_config.json")

        # Verify all parts loaded correctly
        assert len(config.materialized_views) == 3
        assert config.test_limit == 100
        assert len(config.node_mappings) == 2
        assert config.node_mappings[0].properties["title"].transformation == "strip"
        assert config.node_mappings[1].properties["title"].transformation == "uppercase"
        assert len(config.relationship_mappings) == 1

    def test_default_config_directory(self):
        # Test default config directory (should be "config")
        with patch("pathlib.Path.exists", return_value=True):
            manager = ConfigManager()
            assert manager.config_dir == Path("config")

    def test_substitute_env_vars_edge_cases(self, temp_config_dir):
        manager = ConfigManager(temp_config_dir)

        # Test with various edge cases
        edge_cases = {
            "empty_var": "${EMPTY_VAR}",
            "no_vars": "normal string",
            "nested_dict": {"inner": "${NESTED_VAR}"},
            "list_with_vars": ["${LIST_VAR1}", "${LIST_VAR2}"],
        }

        with patch.dict(
            os.environ,
            {
                "EMPTY_VAR": "",
                "NESTED_VAR": "nested_value",
                "LIST_VAR1": "list1",
                "LIST_VAR2": "list2",
            },
        ):
            # Test the internal method directly
            result = manager._substitute_env_vars(
                {
                    "hasura_endpoint": "https://test.com/v1/graphql",
                    "materialized_views": ["test"],
                    "node_mappings": [],
                    "relationship_mappings": [],
                    **edge_cases,
                }
            )

            assert result["empty_var"] == ""
            assert result["no_vars"] == "normal string"
            assert result["nested_dict"]["inner"] == "nested_value"
            assert result["list_with_vars"] == ["list1", "list2"]
