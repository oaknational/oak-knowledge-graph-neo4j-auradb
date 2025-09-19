import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from pipeline.pipeline import (
    Pipeline,
    PipelineStage,
    PipelineProgress,
    PipelineError,
)
from pipeline.config_manager import ConfigManager
from models.config import PipelineConfig, NodeMapping, RelationshipMapping, FieldMapping


class TestPipelineProgress:
    def test_pipeline_progress_creation(self):
        progress = PipelineProgress(
            stage=PipelineStage.EXTRACTING_DATA,
            progress_percent=50.0,
            message="Test message",
            records_processed=10,
            total_records=20,
        )

        assert progress.stage == PipelineStage.EXTRACTING_DATA
        assert progress.progress_percent == 50.0
        assert progress.message == "Test message"
        assert progress.records_processed == 10
        assert progress.total_records == 20


class TestPipelineError:
    def test_pipeline_error_creation(self):
        original_error = ValueError("Original error")
        error = PipelineError(
            PipelineStage.VALIDATING_DATA, "Test error", original_error
        )

        assert error.stage == PipelineStage.VALIDATING_DATA
        assert error.original_error == original_error
        assert "validating_data" in str(error)
        assert "Test error" in str(error)

    def test_pipeline_error_without_original(self):
        error = PipelineError(PipelineStage.LOADING_NEO4J, "Test error")

        assert error.stage == PipelineStage.LOADING_NEO4J
        assert error.original_error is None


class TestPipeline:
    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_config_manager(self):
        return Mock(spec=ConfigManager)

    @pytest.fixture
    def sample_config(self):
        return PipelineConfig(
            hasura_endpoint="https://test.hasura.app/v1/graphql",
            materialized_views=["curriculum_units", "curriculum_lessons"],
            node_mappings=[
                NodeMapping(
                    label="Unit",
                    id_field="unit_id",
                    properties={
                        "id": FieldMapping(
                            source_field="unit_id", target_type="string"
                        ),
                        "title": FieldMapping(
                            source_field="unit_title", target_type="string"
                        ),
                    },
                )
            ],
            relationship_mappings=[
                RelationshipMapping(
                    type="CONTAINS",
                    start_node_id_field="unit_id",
                    end_node_id_field="lesson_id",
                    properties={
                        "order": FieldMapping(
                            source_field="order_in_unit", target_type="int"
                        )
                    },
                )
            ],
        )

    @pytest.fixture
    def mock_progress_callback(self):
        return Mock()

    def test_init_default(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        assert isinstance(pipeline.config_manager, ConfigManager)
        assert pipeline.output_dir == Path(temp_output_dir)
        assert pipeline.current_stage == PipelineStage.LOADING_CONFIG
        assert pipeline.extracted_data == []
        assert pipeline.validated_data == []
        assert pipeline.mapped_data == {}
        assert pipeline.csv_files == {"nodes": [], "relationships": []}

    def test_init_with_custom_components(
        self, mock_config_manager, mock_progress_callback, temp_output_dir
    ):
        pipeline = Pipeline(
            config_manager=mock_config_manager,
            progress_callback=mock_progress_callback,
            output_dir=temp_output_dir,
        )

        assert pipeline.config_manager == mock_config_manager
        assert pipeline.progress_callback == mock_progress_callback

    def test_default_progress_callback(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        progress = PipelineProgress(
            stage=PipelineStage.EXTRACTING_DATA,
            progress_percent=50.0,
            message="Test",
            records_processed=10,
            total_records=20,
        )

        # Should not raise any exceptions
        pipeline._default_progress_callback(progress)

    def test_report_progress(self, mock_progress_callback, temp_output_dir):
        pipeline = Pipeline(
            progress_callback=mock_progress_callback, output_dir=temp_output_dir
        )

        pipeline._report_progress(
            PipelineStage.VALIDATING_DATA, 75.0, "Validating", 15, 20
        )

        assert pipeline.current_stage == PipelineStage.VALIDATING_DATA
        mock_progress_callback.assert_called_once()

        call_args = mock_progress_callback.call_args[0]
        progress = call_args[0]
        assert progress.stage == PipelineStage.VALIDATING_DATA
        assert progress.progress_percent == 75.0
        assert progress.message == "Validating"
        assert progress.records_processed == 15
        assert progress.total_records == 20

    def test_handle_stage_error(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        original_error = ValueError("Original error")

        with pytest.raises(PipelineError) as exc_info:
            pipeline._handle_stage_error(
                PipelineStage.MAPPING_DATA, original_error, "Context message"
            )

        error = exc_info.value
        assert error.stage == PipelineStage.MAPPING_DATA
        assert error.original_error == original_error
        assert "Context message" in str(error)

    @patch.dict(
        os.environ, {"HASURA_API_KEY": "test-key", "OAK_AUTH_TYPE": "oak-admin"}
    )
    @patch("pipeline.auradb_loader.AuraDBLoader")
    @patch("pipeline.loaders.Neo4jLoader")
    @patch("pipeline.transformers.TransformerFactory")
    @patch("pipeline.extractors.HasuraExtractor")
    def test_load_config(
        self,
        mock_hasura_extractor,
        mock_transformer_factory,
        mock_neo4j_loader,
        mock_auradb_loader,
        mock_config_manager,
        sample_config,
        temp_output_dir,
    ):
        mock_config_manager.load_config.return_value = sample_config
        mock_transformer_factory.create_node_transformer.return_value = Mock()

        pipeline = Pipeline(
            config_manager=mock_config_manager, output_dir=temp_output_dir
        )

        result = pipeline.load_config("test_config.json")

        assert result == sample_config
        assert pipeline.config == sample_config
        mock_config_manager.load_config.assert_called_once_with("test_config.json")

        # Verify components are assigned (initialization successful)
        assert pipeline.extractor is not None
        assert pipeline.transformer is not None
        assert pipeline.neo4j_loader is not None
        assert pipeline.auradb_loader is not None

    def test_load_config_error(self, mock_config_manager, temp_output_dir):
        mock_config_manager.load_config.side_effect = ValueError("Config error")
        pipeline = Pipeline(
            config_manager=mock_config_manager, output_dir=temp_output_dir
        )

        with pytest.raises(PipelineError) as exc_info:
            pipeline.load_config("bad_config.json")

        assert exc_info.value.stage == PipelineStage.LOADING_CONFIG

    def test_initialize_components_without_config(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="Configuration must be loaded"):
            pipeline._initialize_components()

    @patch("pipeline.extractors.HasuraExtractor")
    def test_extract_data(
        self, mock_hasura_extractor_class, sample_config, temp_output_dir
    ):
        # Setup mock extractor
        mock_extractor = Mock()
        mock_extractor.extract.return_value = [{"unit_id": "1", "title": "Test Unit"}]
        mock_hasura_extractor_class.return_value = mock_extractor

        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.extractor = mock_extractor

        result = pipeline.extract_data()

        assert len(result) == 1
        assert result[0]["unit_id"] == "1"
        assert pipeline.extracted_data == result
        mock_extractor.extract.assert_called_once_with(sample_config)

    def test_extract_data_without_config(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="Pipeline must be configured"):
            pipeline.extract_data()

    def test_extract_data_error(self, sample_config, temp_output_dir):
        mock_extractor = Mock()
        mock_extractor.extract.side_effect = RuntimeError("Extraction failed")

        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.extractor = mock_extractor

        with pytest.raises(PipelineError) as exc_info:
            pipeline.extract_data()

        assert exc_info.value.stage == PipelineStage.EXTRACTING_DATA

    def test_validate_data(self, sample_config, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.extracted_data = [{"unit_id": "1", "unit_title": "Test"}]

        # Mock validator
        mock_validation_result = Mock()
        mock_validation_result.valid_records = pipeline.extracted_data
        mock_validation_result.invalid_records = []
        mock_validation_result.errors = []

        # Replace validator with mock
        pipeline.validator = Mock()
        pipeline.validator.validate_materialized_view_data.return_value = (
            mock_validation_result
        )
        pipeline.validator.validate_node_data.return_value = mock_validation_result
        pipeline.validator.validate_relationship_data.return_value = (
            mock_validation_result
        )

        result = pipeline.validate_data()

        assert result == mock_validation_result
        assert pipeline.validated_data == pipeline.extracted_data

    def test_validate_data_without_extracted_data(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="No data to validate"):
            pipeline.validate_data()

    def test_validate_data_with_errors(self, sample_config, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.extracted_data = [{"invalid": "data"}]

        # Mock validator with errors
        mock_validation_result = Mock()
        mock_validation_result.valid_records = []
        mock_validation_result.invalid_records = pipeline.extracted_data
        mock_validation_result.errors = ["Validation error 1", "Validation error 2"]

        # Replace validator with mock
        pipeline.validator = Mock()
        pipeline.validator.validate_materialized_view_data.return_value = (
            mock_validation_result
        )
        pipeline.validator.validate_node_data.return_value = mock_validation_result
        pipeline.validator.validate_relationship_data.return_value = (
            mock_validation_result
        )

        with pytest.raises(PipelineError) as exc_info:
            pipeline.validate_data()

        assert exc_info.value.stage == PipelineStage.VALIDATING_DATA
        # Check that pipeline error contains validation error info
        error_msg = str(exc_info.value)
        assert exc_info.value.stage == PipelineStage.VALIDATING_DATA
        assert "errors" in error_msg.lower()

    def test_map_data(self, sample_config, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.validated_data = [{"unit_id": "1", "unit_title": "Test"}]

        # Mock mapper
        pipeline.mapper = Mock()
        pipeline.mapper.map_node_data.return_value = [{"id": "1", "title": "Test"}]
        pipeline.mapper.map_relationship_data.return_value = [
            {"start": "1", "end": "2"}
        ]
        pipeline.mapper.get_data_lineage.return_value = Mock()

        result = pipeline.map_data()

        assert "nodes" in result
        assert "relationships" in result
        assert len(result["nodes"]) == 1
        assert len(result["relationships"]) == 1
        assert pipeline.mapped_data == result

    def test_map_data_without_validated_data(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="No validated data to map"):
            pipeline.map_data()

    def test_transform_to_csv(self, sample_config, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.mapped_data = {
            "nodes": [{"id": "1", "title": "Test"}],
            "relationships": [{"start": "1", "end": "2"}],
        }

        # Mock transformer
        mock_transformer = Mock()
        mock_transformer.transform_nodes_to_csv.return_value = ["nodes.csv"]
        mock_transformer.transform_relationships_to_csv.return_value = ["rels.csv"]
        mock_transformer.validate_csv_format.return_value = True
        pipeline.transformer = mock_transformer

        result = pipeline.transform_to_csv()

        assert "nodes" in result
        assert "relationships" in result
        assert result["nodes"] == ["nodes.csv"]
        assert result["relationships"] == ["rels.csv"]

    def test_transform_to_csv_without_mapped_data(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="No mapped data to transform"):
            pipeline.transform_to_csv()

    def test_transform_to_csv_invalid_format(self, sample_config, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.mapped_data = {"nodes": [{"id": "1"}], "relationships": []}

        # Mock transformer that produces invalid CSV
        mock_transformer = Mock()
        mock_transformer.transform_nodes_to_csv.return_value = ["invalid.csv"]
        mock_transformer.transform_relationships_to_csv.return_value = []
        mock_transformer.validate_csv_format.return_value = False
        pipeline.transformer = mock_transformer

        with pytest.raises(PipelineError) as exc_info:
            pipeline.transform_to_csv()

        assert exc_info.value.stage == PipelineStage.TRANSFORMING_CSV

    def test_load_to_neo4j_auradb(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.csv_files = {"nodes": ["nodes.csv"], "relationships": ["rels.csv"]}
        pipeline.config = Mock()
        pipeline.config.clear_database_before_import = True

        # Mock AuraDB loader
        mock_auradb_loader = Mock()
        mock_auradb_loader.import_csv_files.return_value = {
            "nodes": 10,
            "relationships": 5,
        }
        pipeline.auradb_loader = mock_auradb_loader

        result = pipeline.load_to_neo4j(use_auradb=True)

        assert result["import_type"] == "auradb_direct"
        assert result["statistics"] == {"nodes": 10, "relationships": 5}
        mock_auradb_loader.import_csv_files.assert_called_once_with(
            ["nodes.csv"], ["rels.csv"], clear_before_import=True
        )

    def test_load_to_neo4j_admin_command(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.csv_files = {"nodes": ["nodes.csv"], "relationships": ["rels.csv"]}

        # Mock Neo4j loader
        mock_neo4j_loader = Mock()
        mock_neo4j_loader.generate_import_command.return_value = (
            "neo4j-admin import ..."
        )
        mock_neo4j_loader.generate_import_summary.return_value = {"total_files": 2}
        pipeline.neo4j_loader = mock_neo4j_loader

        result = pipeline.load_to_neo4j(use_auradb=False)

        assert result["import_type"] == "neo4j_admin"
        assert result["command"] == "neo4j-admin import ..."
        assert result["summary"] == {"total_files": 2}

    def test_load_to_neo4j_without_csv_files(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="No CSV files to load"):
            pipeline.load_to_neo4j()

    @patch.object(Pipeline, "load_config")
    @patch.object(Pipeline, "extract_data")
    @patch.object(Pipeline, "validate_data")
    @patch.object(Pipeline, "map_data")
    @patch.object(Pipeline, "transform_to_csv")
    @patch.object(Pipeline, "load_to_neo4j")
    def test_run_full_pipeline(
        self,
        mock_load_neo4j,
        mock_transform,
        mock_map,
        mock_validate,
        mock_extract,
        mock_load_config,
        sample_config,
        temp_output_dir,
    ):
        # Setup mocks
        mock_load_config.return_value = sample_config
        mock_extract.return_value = [{"unit_id": "1"}]
        mock_validation_result = Mock()
        mock_validation_result.valid_records = [{"unit_id": "1"}]
        mock_validation_result.invalid_records = []
        mock_validation_result.errors = []
        mock_validate.return_value = mock_validation_result
        mock_map.return_value = {"nodes": [{"id": "1"}], "relationships": []}
        mock_transform.return_value = {"nodes": ["nodes.csv"], "relationships": []}
        mock_load_neo4j.return_value = {"import_type": "neo4j_admin"}

        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.data_lineage = Mock()
        pipeline.data_lineage.transformations = []

        result = pipeline.run_full_pipeline("test_config.json")

        # Verify all stages were called
        mock_load_config.assert_called_once_with("test_config.json")
        mock_extract.assert_called_once()
        mock_validate.assert_called_once()
        mock_map.assert_called_once()
        mock_transform.assert_called_once()
        mock_load_neo4j.assert_called_once_with(False)

        # Verify result structure
        assert "config" in result
        assert "extraction" in result
        assert "validation" in result
        assert "mapping" in result
        assert "csv_files" in result
        assert "neo4j_import" in result
        assert "output_directory" in result

    def test_run_full_pipeline_with_pipeline_error(self, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with patch.object(pipeline, "load_config") as mock_load_config:
            mock_load_config.side_effect = PipelineError(
                PipelineStage.LOADING_CONFIG, "Config error"
            )

            with pytest.raises(PipelineError):
                pipeline.run_full_pipeline("test_config.json")

    def test_run_partial_pipeline_valid_stages(self, sample_config, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with patch.object(pipeline, "load_config") as mock_load_config:
            mock_load_config.return_value = sample_config

            with patch.object(pipeline, "extract_data") as mock_extract:
                mock_extract.return_value = [{"unit_id": "1"}]

                result = pipeline.run_partial_pipeline(
                    "test_config.json", ["config", "extract"]
                )

                assert "config" in result
                assert "extract" in result
                assert result["config"] == sample_config
                assert result["extract"] == [{"unit_id": "1"}]

    @patch.dict(
        os.environ, {"HASURA_API_KEY": "test-key", "OAK_AUTH_TYPE": "oak-admin"}
    )
    @patch("pipeline.transformers.TransformerFactory")
    def test_run_partial_pipeline_invalid_stage(
        self, mock_transformer_factory, temp_output_dir
    ):
        mock_transformer_factory.create_node_transformer.return_value = Mock()
        pipeline = Pipeline(output_dir=temp_output_dir)

        # Should validate stages before attempting to load config
        with pytest.raises(ValueError, match="Invalid stage: invalid"):
            pipeline.run_partial_pipeline("test_config.json", ["invalid"])

    def test_run_partial_pipeline_auto_load_config(
        self, sample_config, temp_output_dir
    ):
        pipeline = Pipeline(output_dir=temp_output_dir)

        with patch.object(pipeline, "load_config") as mock_load_config:
            mock_load_config.return_value = sample_config

            with patch.object(pipeline, "extract_data") as mock_extract:
                mock_extract.return_value = [{"unit_id": "1"}]

                # Request extract without explicitly requesting config
                result = pipeline.run_partial_pipeline("test_config.json", ["extract"])

                # Config should be loaded automatically
                mock_load_config.assert_called_once_with("test_config.json")
                assert "extract" in result

    def test_get_pipeline_state(self, sample_config, temp_output_dir):
        pipeline = Pipeline(output_dir=temp_output_dir)
        pipeline.config = sample_config
        pipeline.extracted_data = [{"unit_id": "1"}]
        pipeline.validated_data = [{"unit_id": "1"}]
        pipeline.mapped_data = {"nodes": [], "relationships": []}
        pipeline.csv_files = {"nodes": ["nodes.csv"], "relationships": []}
        pipeline.current_stage = PipelineStage.TRANSFORMING_CSV

        state = pipeline.get_pipeline_state()

        assert state["current_stage"] == "transforming_csv"
        assert state["config_loaded"] is True
        assert state["data_extracted"] == 1
        assert state["data_validated"] == 1
        assert state["data_mapped"] is True
        assert state["csv_files_generated"] == 1
        assert state["output_directory"] == str(pipeline.output_dir)

    def test_ensure_output_dir_creates_directory(self):
        with tempfile.TemporaryDirectory() as temp_parent:
            output_dir = os.path.join(temp_parent, "new_pipeline_output")
            pipeline = Pipeline(output_dir=output_dir)

            assert os.path.exists(output_dir)
            assert pipeline.output_dir == Path(output_dir)
