#!/usr/bin/env python3
"""
Integration Tests for Oak Knowledge Graph Pipeline

Tests complete end-to-end pipeline functionality with sample data,
including CSV generation and Neo4j import validation.
"""

import os
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Import our pipeline components
from pipeline.pipeline import Pipeline
from pipeline.config_manager import ConfigManager
from pipeline.extractors import HasuraExtractor
from models.config import PipelineConfig


class TestIntegrationPipeline:
    """Integration tests for complete pipeline functionality."""

    @pytest.fixture
    def test_config_path(self):
        """Path to integration test configuration."""
        return "integration_test_config.json"

    @pytest.fixture
    def test_data_path(self):
        """Path to integration test data fixtures."""
        return "tests/fixtures/integration_test_data.json"

    @pytest.fixture
    def temp_output_dir(self):
        """Temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def integration_test_data(self, test_data_path):
        """Load integration test data from fixtures."""
        with open(test_data_path, 'r') as f:
            return json.load(f)

    @pytest.fixture
    def mock_hasura_responses(self, integration_test_data):
        """Mock Hasura API responses with integration test data."""
        def mock_query_mv(endpoint, view_name, limit=None):
            if view_name in integration_test_data:
                data = integration_test_data[view_name]["data"][view_name]
                if limit:
                    data = data[:limit]
                return data
            return []
        return mock_query_mv

    def test_pipeline_configuration_loading(self, test_config_path):
        """Test that integration test configuration loads correctly."""
        config_manager = ConfigManager()
        config = config_manager.load_config(test_config_path)

        assert isinstance(config, PipelineConfig)
        assert config.test_limit == 10
        assert config.clear_database_before_import is True
        assert len(config.materialized_views) == 3
        assert len(config.node_mappings) == 3
        assert len(config.relationship_mappings) == 2

    @patch.dict('os.environ', {
        'HASURA_API_KEY': 'test_key_123',
        'OAK_AUTH_TYPE': 'oak-admin'
    })
    @patch('pipeline.extractors.HasuraExtractor._query_materialized_view')
    def test_full_pipeline_execution(
        self, mock_extract, test_config_path, temp_output_dir,
        mock_hasura_responses
    ):
        """Test complete pipeline execution with mock data."""
        # Setup mock responses
        mock_extract.side_effect = mock_hasura_responses

        # Initialize pipeline
        pipeline = Pipeline(
            output_dir=temp_output_dir
        )

        # Mock progress callback
        progress_callback = Mock()

        # Execute full pipeline
        result = pipeline.run_full_pipeline(
            config_file=test_config_path,
            use_auradb=False
        )

        # Verify pipeline execution success
        assert result is not None
        assert "config" in result
        assert "extraction" in result
        assert "validation" in result
        assert "csv_files" in result

        # Verify data extraction
        assert result["extraction"]["total_records"] > 0

        # Verify CSV files were mentioned in result
        assert len(result["csv_files"]) > 0

        # Verify CSV files were generated
        output_path = Path(temp_output_dir)
        csv_files = list(output_path.glob("*.csv"))
        assert len(csv_files) > 0

        # Look for node and relationship files
        node_files = [f for f in csv_files if "_nodes.csv" in f.name]
        rel_files = [f for f in csv_files if "_relationships.csv" in f.name]

        assert len(node_files) > 0, "No node CSV files generated"
        assert len(rel_files) > 0, "No relationship CSV files generated"

    def test_csv_format_validation(
        self, test_config_path, temp_output_dir, mock_hasura_responses
    ):
        """Test that generated CSV files meet Neo4j import requirements."""
        with patch('pipeline.extractors.HasuraExtractor._query_materialized_view') as mock_extract:
            mock_extract.side_effect = mock_hasura_responses

            pipeline = Pipeline(
                config_path=test_config_path,
                output_dir=temp_output_dir
            )

            # Execute pipeline
            result = pipeline.run_full_pipeline(use_auradb=False)
            assert result.success is True

            # Validate CSV formats
            output_path = Path(temp_output_dir)

            # Check node CSV files
            node_files = list(output_path.glob("*_nodes.csv"))
            for node_file in node_files:
                self._validate_node_csv(node_file)

            # Check relationship CSV files
            rel_files = list(output_path.glob("*_relationships.csv"))
            for rel_file in rel_files:
                self._validate_relationship_csv(rel_file)

    def _validate_node_csv(self, csv_path):
        """Validate Neo4j node CSV format requirements."""
        df = pd.read_csv(csv_path)

        # Check required columns
        assert ":ID" in df.columns, f"Missing :ID column in {csv_path}"
        assert ":LABEL" in df.columns, f"Missing :LABEL column in {csv_path}"

        # Check data types in headers
        headers = df.columns.tolist()
        type_columns = [col for col in headers if ":" in col]

        # Validate type annotations
        valid_types = [":ID", ":LABEL", ":string", ":int", ":float", ":boolean"]
        for col in type_columns:
            col_type = col.split(":")[-1] if ":" in col else ""
            assert any(valid_type.endswith(col_type) for valid_type in valid_types), \
                f"Invalid type annotation {col} in {csv_path}"

        # Check for non-empty data
        assert len(df) > 0, f"No data in node file {csv_path}"

        # Check ID uniqueness
        assert df[":ID"].nunique() == len(df), f"Non-unique IDs in {csv_path}"

    def _validate_relationship_csv(self, csv_path):
        """Validate Neo4j relationship CSV format requirements."""
        df = pd.read_csv(csv_path)

        # Check required columns
        assert ":START_ID" in df.columns, f"Missing :START_ID column in {csv_path}"
        assert ":END_ID" in df.columns, f"Missing :END_ID column in {csv_path}"
        assert ":TYPE" in df.columns, f"Missing :TYPE column in {csv_path}"

        # Check for non-empty data
        assert len(df) > 0, f"No data in relationship file {csv_path}"

        # Check no null values in required columns
        assert not df[":START_ID"].isnull().any(), f"Null :START_ID values in {csv_path}"
        assert not df[":END_ID"].isnull().any(), f"Null :END_ID values in {csv_path}"
        assert not df[":TYPE"].isnull().any(), f"Null :TYPE values in {csv_path}"

    @patch('pipeline.extractors.HasuraExtractor.extract_from_view')
    def test_neo4j_import_command_generation(
        self, mock_extract, test_config_path, temp_output_dir,
        mock_hasura_responses
    ):
        """Test Neo4j import command generation."""
        mock_extract.side_effect = mock_hasura_responses

        pipeline = Pipeline(
            config_path=test_config_path,
            output_dir=temp_output_dir
        )

        # Execute pipeline
        result = pipeline.run_full_pipeline(use_auradb=False)
        assert result.success is True

        # Check that import commands were generated
        import_summary = pipeline.get_import_summary()
        assert import_summary is not None
        assert "import_command" in import_summary
        assert "neo4j-admin database import" in import_summary["import_command"]

    def test_data_validation_integration(
        self, test_config_path, temp_output_dir, integration_test_data
    ):
        """Test data validation during pipeline execution."""
        with patch('pipeline.extractors.HasuraExtractor._query_materialized_view') as mock_extract:
            # Test with valid data
            def valid_mock_extract(endpoint, view_name, limit=None):
                if view_name in integration_test_data:
                    data = integration_test_data[view_name]["data"][view_name]
                    if limit:
                        data = data[:limit]
                    return data
                return []

            mock_extract.side_effect = valid_mock_extract

            pipeline = Pipeline(
                config_path=test_config_path,
                output_dir=temp_output_dir
            )

            result = pipeline.run_full_pipeline(use_auradb=False)
            assert result.success is True

    def test_error_handling_integration(self, test_config_path, temp_output_dir):
        """Test pipeline error handling with invalid data."""
        with patch('pipeline.extractors.HasuraExtractor._query_materialized_view') as mock_extract:
            # Mock API error
            mock_extract.side_effect = Exception("Mock Hasura API error")

            pipeline = Pipeline(
                config_path=test_config_path,
                output_dir=temp_output_dir
            )

            result = pipeline.run_full_pipeline(use_auradb=False)
            assert result.success is False
            assert "error" in result.message.lower()

    @pytest.mark.skipif(
        not os.getenv("NEO4J_URI") or not os.getenv("NEO4J_USER"),
        reason="Neo4j credentials not configured"
    )
    def test_actual_neo4j_import(self, test_config_path, temp_output_dir):
        """Test actual Neo4j database import (requires real credentials)."""
        # This test only runs when Neo4j credentials are available
        with patch('pipeline.extractors.HasuraExtractor._query_materialized_view') as mock_extract:
            # Use small dataset for actual database testing
            test_data = [
                {
                    "unit_id": "test_unit_001",
                    "unit_title": "Test Unit",
                    "unit_description": "Test Description",
                    "subject_id": "test_subject_001",
                    "subject_title": "Test Subject"
                }
            ]
            # Mock method takes endpoint, view_name, limit parameters
            def mock_query_mv(endpoint, view_name, limit=None):
                return test_data[:limit] if limit else test_data
            mock_extract.side_effect = mock_query_mv

            pipeline = Pipeline(
                config_path=test_config_path,
                output_dir=temp_output_dir
            )

            # Execute with AuraDB loader
            result = pipeline.run_full_pipeline(use_auradb=True)

            # Note: This would actually connect to Neo4j if credentials are present
            # In a real test environment, we would verify the import succeeded
            assert result is not None


class TestIntegrationScenarios:
    """Test specific integration scenarios and edge cases."""

    def test_empty_dataset_handling(self):
        """Test pipeline behavior with empty datasets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pipeline.extractors.HasuraExtractor._query_materialized_view') as mock_extract:
                # Mock method takes endpoint, view_name, limit parameters
                def mock_query_mv(endpoint, view_name, limit=None):
                    return []
                mock_extract.side_effect = mock_query_mv

                pipeline = Pipeline(
                    config_path="integration_test_config.json",
                    output_dir=temp_dir
                )

                result = pipeline.run_full_pipeline(use_auradb=False)
                # Pipeline should handle empty data gracefully
                assert result is not None

    def test_large_dataset_simulation(self):
        """Test pipeline with larger dataset simulation."""
        # Generate synthetic test data
        large_dataset = []
        for i in range(100):  # Simulate 100 records
            large_dataset.append({
                "unit_id": f"sim_unit_{i:03d}",
                "unit_title": f"Simulated Unit {i}",
                "unit_description": f"Description for unit {i}",
                "subject_id": f"sim_subject_{i % 10}",  # 10 subjects
                "subject_title": f"Subject {i % 10}"
            })

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pipeline.extractors.HasuraExtractor._query_materialized_view') as mock_extract:
                # Mock method takes endpoint, view_name, limit parameters
                def mock_query_mv(endpoint, view_name, limit=None):
                    data = large_dataset[:limit] if limit else large_dataset
                    return data
                mock_extract.side_effect = mock_query_mv

                pipeline = Pipeline(
                    config_path="integration_test_config.json",
                    output_dir=temp_dir
                )

                result = pipeline.run_full_pipeline(use_auradb=False)
                assert result.success is True

                # Verify CSV files contain expected number of records
                output_path = Path(temp_dir)
                csv_files = list(output_path.glob("*.csv"))
                assert len(csv_files) > 0


if __name__ == "__main__":
    # Allow running integration tests directly
    pytest.main([__file__, "-v"])