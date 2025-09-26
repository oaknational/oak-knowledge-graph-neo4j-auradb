#!/usr/bin/env python3
"""
Simple test for the simplified batch job architecture.
"""

import os
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from config_manager import ConfigManager, ConfigurationError
from data_cleaner import DataCleaner
from schema_mapper import SchemaMapper

# Load environment variables from .env file
load_dotenv()


def test_config_manager():
    """Test simplified config manager."""
    print("Testing ConfigManager...")

    # Create a temporary config file
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        config_file = "test_config.json"
        config_path = config_dir / config_file

        # Create test configuration
        test_config = {
            "hasura_endpoint": "https://api.example.com/v1/graphql",
            "materialized_views": {
                "curriculum_mv": ["id", "curriculum_title", "subject_name"],
                "lessons_mv": ["lesson_id", "curriculum_id", "lesson_title"],
            },
            "join_strategy": {
                "type": "single_source",
                "primary_mv": "curriculum_mv",
                "joins": [],
            },
            "schema_mapping": {
                "nodes": {
                    "Curriculum": {
                        "id_field": "id",
                        "properties": {
                            "title": "curriculum_title",
                            "subject": "subject_name",
                        },
                    }
                },
                "relationships": {
                    "HAS_LESSON": {
                        "start_node_field": "curriculum_id",
                        "end_node_field": "lesson_id",
                        "properties": {},
                    }
                },
            },
        }

        # Save config
        with open(config_path, "w") as f:
            json.dump(test_config, f, indent=2)

        # Test loading
        config_manager = ConfigManager(str(config_dir))
        loaded_config = config_manager.load_config(config_file)

        # Verify
        assert loaded_config["hasura_endpoint"] == test_config["hasura_endpoint"]
        assert loaded_config["materialized_views"] == test_config["materialized_views"]
        assert "schema_mapping" in loaded_config

    print("✅ ConfigManager test passed")


def test_data_cleaner():
    """Test data cleaner with sample CSV."""
    print("Testing DataCleaner...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample CSV
        csv_content = """id,title,description,status
1,Test Course, Some description ,active
2,Another Course,  ,inactive
3,,Empty title,active"""

        csv_path = Path(temp_dir) / "test_data.csv"
        with open(csv_path, "w") as f:
            f.write(csv_content)

        # Test cleaning
        cleaner = DataCleaner(output_dir=temp_dir)
        cleaned_path = cleaner.clean_data(str(csv_path))

        # Verify cleaned file exists
        assert Path(cleaned_path).exists()

        print(f"✅ DataCleaner test passed: {cleaned_path}")


def test_schema_mapper():
    """Test schema mapper with sample data."""
    print("Testing SchemaMapper...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample CSV
        csv_content = """curriculum_id,curriculum_title,lesson_id,lesson_title,subject_name
1,Math Basics,101,Introduction to Numbers,Mathematics
1,Math Basics,102,Addition and Subtraction,Mathematics
2,Science Fun,201,What is Science,Science"""

        csv_path = Path(temp_dir) / "test_mapping.csv"
        with open(csv_path, "w") as f:
            f.write(csv_content)

        # Test schema mapping
        schema_mapping = {
            "nodes": {
                "Curriculum": {
                    "id_field": "curriculum_id",
                    "properties": {
                        "title": "curriculum_title",
                        "subject": "subject_name",
                    },
                },
                "Lesson": {
                    "id_field": "lesson_id",
                    "properties": {"title": "lesson_title"},
                },
            },
            "relationships": {
                "HAS_LESSON": {
                    "start_node_field": "curriculum_id",
                    "end_node_field": "lesson_id",
                    "properties": {},
                }
            },
        }

        mapper = SchemaMapper()
        mapped_data = mapper.map_from_csv(str(csv_path), schema_mapping)

        # Verify structure
        assert "node_files" in mapped_data
        assert "relationship_files" in mapped_data
        assert len(mapped_data["node_files"]) > 0
        assert len(mapped_data["relationship_files"]) > 0

        print("✅ SchemaMapper test passed")


def test_invalid_config():
    """Test config validation."""
    print("Testing config validation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        config_file = "invalid_config.json"
        config_path = config_dir / config_file

        # Create invalid configuration (missing required keys)
        invalid_config = {
            "hasura_endpoint": "https://api.example.com/v1/graphql"
            # Missing materialized_views and schema_mapping
        }

        with open(config_path, "w") as f:
            json.dump(invalid_config, f, indent=2)

        # Test validation failure
        config_manager = ConfigManager(str(config_dir))
        try:
            config_manager.load_config(config_file)
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError as e:
            assert "materialized_views" in str(e)

    print("✅ Config validation test passed")


def main():
    """Run all tests."""
    print("🧪 Running simplified batch job tests")
    print("=" * 50)

    try:
        test_config_manager()
        test_data_cleaner()
        test_schema_mapper()
        test_invalid_config()

        print("=" * 50)
        print("✅ All tests passed!")
        print("🎉 Simplified architecture is working correctly")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
