from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from models.config import PipelineConfig
from pipeline.config_manager import ConfigManager, ConfigurationError
from pipeline.extractors import HasuraExtractor
from pipeline.validators import DataValidator, ValidationResult
from pipeline.mappers import SchemaMapper, DataLineage
from pipeline.transformers import CSVTransformer, TransformerFactory
from pipeline.loaders import Neo4jLoader
from pipeline.auradb_loader import AuraDBLoader


class PipelineStage(Enum):
    LOADING_CONFIG = "loading_config"
    EXTRACTING_DATA = "extracting_data"
    VALIDATING_DATA = "validating_data"
    MAPPING_DATA = "mapping_data"
    TRANSFORMING_CSV = "transforming_csv"
    LOADING_NEO4J = "loading_neo4j"
    COMPLETE = "complete"


@dataclass
class PipelineProgress:
    stage: PipelineStage
    progress_percent: float
    message: str
    records_processed: int = 0
    total_records: int = 0


class PipelineError(Exception):
    def __init__(
        self, stage: PipelineStage, message: str, original_error: Exception = None
    ):
        self.stage = stage
        self.original_error = original_error
        super().__init__(f"Pipeline failed at {stage.value}: {message}")


class Pipeline:
    def __init__(
        self,
        config_manager: ConfigManager = None,
        progress_callback: Callable[[PipelineProgress], None] = None,
        output_dir: str = "data",
    ):
        self.config_manager = config_manager or ConfigManager()
        self.progress_callback = progress_callback or self._default_progress_callback
        self.output_dir = Path(output_dir)

        # Initialize components (dependency injection)
        self.config: Optional[PipelineConfig] = None
        self.extractor: Optional[HasuraExtractor] = None
        self.validator = DataValidator()
        self.mapper = SchemaMapper()
        self.transformer: Optional[CSVTransformer] = None
        self.neo4j_loader: Optional[Neo4jLoader] = None
        self.auradb_loader: Optional[AuraDBLoader] = None

        # Pipeline state
        self.current_stage = PipelineStage.LOADING_CONFIG
        self.extracted_data: List[Dict] = []
        self.validated_data: List[Dict] = []
        self.mapped_data: Dict[str, Any] = {}
        self.csv_files: Dict[str, List[str]] = {"nodes": [], "relationships": []}
        self.data_lineage = DataLineage()

        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _default_progress_callback(self, progress: PipelineProgress) -> None:
        """Default progress callback that prints to console."""
        print(
            f"[{progress.stage.value}] {progress.progress_percent:.1f}% - "
            f"{progress.message}"
        )
        if progress.total_records > 0:
            print(f"  Records: {progress.records_processed}/{progress.total_records}")

    def _report_progress(
        self,
        stage: PipelineStage,
        percent: float,
        message: str,
        records_processed: int = 0,
        total_records: int = 0,
    ) -> None:
        """Report progress via callback."""
        self.current_stage = stage
        progress = PipelineProgress(
            stage=stage,
            progress_percent=percent,
            message=message,
            records_processed=records_processed,
            total_records=total_records,
        )
        self.progress_callback(progress)

    def _handle_stage_error(
        self, stage: PipelineStage, error: Exception, context: str = ""
    ) -> None:
        """Handle errors with context and fail fast."""
        error_msg = f"{context}: {str(error)}" if context else str(error)

        # Log original error for debugging
        if hasattr(error, "__traceback__"):
            print(f"Original error in {stage.value}: {error}")

        raise PipelineError(stage, error_msg, error)

    def load_config(self, config_file: str) -> PipelineConfig:
        """Load and validate pipeline configuration."""
        try:
            self._report_progress(
                PipelineStage.LOADING_CONFIG, 10, "Loading configuration file"
            )

            self.config = self.config_manager.load_config(config_file)

            self._report_progress(
                PipelineStage.LOADING_CONFIG, 50, "Validating configuration"
            )

            # Initialize components with config
            self._initialize_components()

            self._report_progress(
                PipelineStage.LOADING_CONFIG, 100, "Configuration loaded successfully"
            )

            return self.config

        except (ConfigurationError, ValueError) as e:
            self._handle_stage_error(
                PipelineStage.LOADING_CONFIG, e, "Configuration validation failed"
            )

    def _initialize_components(self) -> None:
        """Initialize pipeline components with dependency injection."""
        if not self.config:
            raise ValueError(
                "Configuration must be loaded before initializing components"
            )

        # Initialize extractor with Oak authentication
        self.extractor = HasuraExtractor()

        # Initialize transformer with CSV strategy
        self.transformer = TransformerFactory.create_node_transformer("csv")

        # Initialize loaders
        self.neo4j_loader = Neo4jLoader(import_dir=str(self.output_dir))
        self.auradb_loader = AuraDBLoader()

    def extract_data(self) -> List[Dict]:
        """Extract data from Hasura materialized views."""
        if not self.config or not self.extractor:
            raise ValueError("Pipeline must be configured before extraction")

        try:
            self._report_progress(
                PipelineStage.EXTRACTING_DATA, 10, "Starting data extraction"
            )

            self.extracted_data = self.extractor.extract(self.config)

            self._report_progress(
                PipelineStage.EXTRACTING_DATA,
                100,
                f"Extracted {len(self.extracted_data)} records",
                len(self.extracted_data),
                len(self.extracted_data),
            )

            return self.extracted_data

        except Exception as e:
            self._handle_stage_error(
                PipelineStage.EXTRACTING_DATA, e, "Data extraction failed"
            )

    def validate_data(self) -> ValidationResult:
        """Validate extracted data against Pydantic models."""
        if not self.extracted_data:
            raise ValueError("No data to validate - run extract_data() first")

        try:
            self._report_progress(
                PipelineStage.VALIDATING_DATA, 10, "Starting data validation"
            )

            # Validate materialized view data
            # For now, validate all data as a single collection
            validation_result = self.validator.validate_materialized_view_data(
                self.extracted_data, "combined_views"
            )

            self._report_progress(
                PipelineStage.VALIDATING_DATA, 50, "Validating against node mappings"
            )

            # Validate against node mappings
            for node_mapping in self.config.node_mappings:
                node_validation = self.validator.validate_node_data(
                    validation_result.valid_records, node_mapping
                )
                if node_validation.errors:
                    validation_result.errors.extend(node_validation.errors)

            self._report_progress(
                PipelineStage.VALIDATING_DATA,
                80,
                "Validating against relationship mappings",
            )

            # Validate against relationship mappings
            for rel_mapping in self.config.relationship_mappings:
                rel_validation = self.validator.validate_relationship_data(
                    validation_result.valid_records, rel_mapping
                )
                if rel_validation.errors:
                    validation_result.errors.extend(rel_validation.errors)

            # Store validated data
            self.validated_data = validation_result.valid_records

            # Fail fast if validation errors
            if validation_result.errors:
                error_summary = (
                    f"Validation failed with {len(validation_result.errors)} errors"
                )
                self._handle_stage_error(
                    PipelineStage.VALIDATING_DATA, ValueError(error_summary)
                )

            self._report_progress(
                PipelineStage.VALIDATING_DATA,
                100,
                f"Validated {len(self.validated_data)} records successfully",
                len(self.validated_data),
                len(self.extracted_data),
            )

            return validation_result

        except Exception as e:
            self._handle_stage_error(
                PipelineStage.VALIDATING_DATA, e, "Data validation failed"
            )

    def map_data(self) -> Dict[str, Any]:
        """Apply schema mappings to transform data."""
        if not self.validated_data:
            raise ValueError("No validated data to map - run validate_data() first")

        try:
            self._report_progress(
                PipelineStage.MAPPING_DATA, 10, "Starting schema mapping"
            )

            mapped_nodes = []
            mapped_relationships = []

            # Map nodes
            progress_step = 80 / (
                len(self.config.node_mappings) + len(self.config.relationship_mappings)
            )
            current_progress = 10

            for node_mapping in self.config.node_mappings:
                self._report_progress(
                    PipelineStage.MAPPING_DATA,
                    current_progress,
                    f"Mapping {node_mapping.label} nodes",
                )

                node_data = self.mapper.map_node_data(self.validated_data, node_mapping)
                mapped_nodes.extend(node_data)

                current_progress += progress_step

            # Map relationships
            for rel_mapping in self.config.relationship_mappings:
                self._report_progress(
                    PipelineStage.MAPPING_DATA,
                    current_progress,
                    f"Mapping {rel_mapping.type} relationships",
                )

                rel_data = self.mapper.map_relationship_data(
                    self.validated_data, rel_mapping
                )
                mapped_relationships.extend(rel_data)

                current_progress += progress_step

            self.mapped_data = {
                "nodes": mapped_nodes,
                "relationships": mapped_relationships,
            }

            # Store data lineage
            self.data_lineage = self.mapper.get_data_lineage()

            total_mapped = len(mapped_nodes) + len(mapped_relationships)
            self._report_progress(
                PipelineStage.MAPPING_DATA,
                100,
                f"Mapped {total_mapped} items ({len(mapped_nodes)} nodes, "
                f"{len(mapped_relationships)} relationships)",
            )

            return self.mapped_data

        except Exception as e:
            self._handle_stage_error(
                PipelineStage.MAPPING_DATA, e, "Schema mapping failed"
            )

    def transform_to_csv(self) -> Dict[str, List[str]]:
        """Transform mapped data to Neo4j CSV format."""
        if not self.mapped_data:
            raise ValueError("No mapped data to transform - run map_data() first")

        try:
            self._report_progress(
                PipelineStage.TRANSFORMING_CSV, 10, "Starting CSV transformation"
            )

            # Transform nodes to CSV
            if self.mapped_data["nodes"]:
                self._report_progress(
                    PipelineStage.TRANSFORMING_CSV, 30, "Transforming nodes to CSV"
                )

                node_files = self.transformer.transform_nodes_to_csv(
                    self.mapped_data["nodes"],
                    self.config.node_mappings,
                    str(self.output_dir),
                )
                self.csv_files["nodes"] = node_files

            # Transform relationships to CSV
            if self.mapped_data["relationships"]:
                self._report_progress(
                    PipelineStage.TRANSFORMING_CSV,
                    60,
                    "Transforming relationships to CSV",
                )

                rel_files = self.transformer.transform_relationships_to_csv(
                    self.mapped_data["relationships"],
                    self.config.relationship_mappings,
                    str(self.output_dir),
                )
                self.csv_files["relationships"] = rel_files

            # Validate CSV format
            self._report_progress(
                PipelineStage.TRANSFORMING_CSV, 90, "Validating CSV format"
            )

            all_files = self.csv_files["nodes"] + self.csv_files["relationships"]
            for csv_file in all_files:
                if not self.transformer.validate_csv_format(csv_file):
                    raise ValueError(f"Invalid CSV format: {csv_file}")

            self._report_progress(
                PipelineStage.TRANSFORMING_CSV,
                100,
                f"Generated {len(all_files)} CSV files",
            )

            return self.csv_files

        except Exception as e:
            self._handle_stage_error(
                PipelineStage.TRANSFORMING_CSV, e, "CSV transformation failed"
            )

    def load_to_neo4j(self, use_auradb: bool = False) -> Dict[str, Any]:
        """Load CSV files to Neo4j database."""
        if not self.csv_files["nodes"] and not self.csv_files["relationships"]:
            raise ValueError("No CSV files to load - run transform_to_csv() first")

        try:
            self._report_progress(
                PipelineStage.LOADING_NEO4J, 10, "Starting Neo4j load"
            )

            if use_auradb:
                # Direct database import via AuraDB
                self._report_progress(
                    PipelineStage.LOADING_NEO4J, 30, "Importing to AuraDB"
                )

                import_stats = self.auradb_loader.import_csv_files(
                    self.csv_files["nodes"],
                    self.csv_files["relationships"],
                    clear_before_import=self.config.clear_database_before_import,
                )

                result = {"import_type": "auradb_direct", "statistics": import_stats}

            else:
                # Generate import command for neo4j-admin
                self._report_progress(
                    PipelineStage.LOADING_NEO4J, 30, "Generating import command"
                )

                import_command = self.neo4j_loader.generate_import_command(
                    self.csv_files["nodes"], self.csv_files["relationships"]
                )

                # Generate import summary
                summary = self.neo4j_loader.generate_import_summary(
                    self.csv_files["nodes"], self.csv_files["relationships"]
                )

                result = {
                    "import_type": "neo4j_admin",
                    "command": import_command,
                    "summary": summary,
                }

            self._report_progress(
                PipelineStage.LOADING_NEO4J, 100, "Neo4j load completed"
            )

            return result

        except Exception as e:
            self._handle_stage_error(
                PipelineStage.LOADING_NEO4J, e, "Neo4j load failed"
            )

    def run_full_pipeline(
        self, config_file: str, use_auradb: bool = False
    ) -> Dict[str, Any]:
        """Run the complete pipeline from configuration to Neo4j import."""
        try:
            # Stage 1: Load configuration
            config = self.load_config(config_file)

            # Stage 2: Extract data
            extracted_data = self.extract_data()

            # Stage 3: Validate data
            validation_result = self.validate_data()

            # Stage 4: Map data
            mapped_data = self.map_data()

            # Stage 5: Transform to CSV
            csv_files = self.transform_to_csv()

            # Stage 6: Load to Neo4j
            load_result = self.load_to_neo4j(use_auradb)

            # Pipeline complete
            self._report_progress(
                PipelineStage.COMPLETE, 100, "Pipeline completed successfully"
            )

            return {
                "config": config.model_dump(),
                "extraction": {
                    "total_records": len(extracted_data),
                    "materialized_views": config.materialized_views,
                },
                "validation": {
                    "valid_records": len(validation_result.valid_records),
                    "invalid_records": len(validation_result.invalid_records),
                    "errors": validation_result.errors,
                },
                "mapping": {
                    "nodes_mapped": len(mapped_data["nodes"]),
                    "relationships_mapped": len(mapped_data["relationships"]),
                    "data_lineage": self.data_lineage.transformations,
                },
                "csv_files": csv_files,
                "neo4j_import": load_result,
                "output_directory": str(self.output_dir),
            }

        except PipelineError:
            # Re-raise pipeline errors (already have context)
            raise
        except Exception as e:
            # Handle unexpected errors
            self._handle_stage_error(
                self.current_stage, e, "Unexpected error in pipeline"
            )

    def run_partial_pipeline(
        self, config_file: str, stages: List[str]
    ) -> Dict[str, Any]:
        """Run only specified stages of the pipeline."""
        valid_stages = {
            "config": self.load_config,
            "extract": self.extract_data,
            "validate": self.validate_data,
            "map": self.map_data,
            "transform": self.transform_to_csv,
            "load": lambda: self.load_to_neo4j(use_auradb=False),
        }

        results = {}

        # Always load config first if any other stage is requested
        if stages and "config" not in stages:
            self.load_config(config_file)

        for stage in stages:
            if stage not in valid_stages:
                raise ValueError(
                    f"Invalid stage: {stage}. Valid stages: {list(valid_stages.keys())}"
                )

            try:
                if stage == "config":
                    results[stage] = valid_stages[stage](config_file)
                else:
                    results[stage] = valid_stages[stage]()
            except PipelineError:
                raise
            except Exception as e:
                stage_enum = getattr(PipelineStage, stage.upper(), self.current_stage)
                self._handle_stage_error(
                    stage_enum, e, f"Failed to execute stage: {stage}"
                )

        # Add extracted data to results for debugging
        if hasattr(self, "extracted_data") and self.extracted_data:
            results["extracted_data"] = self.extracted_data

        return results

    def get_pipeline_state(self) -> Dict[str, Any]:
        """Get current pipeline state and progress."""
        return {
            "current_stage": self.current_stage.value,
            "config_loaded": self.config is not None,
            "data_extracted": len(self.extracted_data),
            "data_validated": len(self.validated_data),
            "data_mapped": bool(self.mapped_data),
            "csv_files_generated": len(self.csv_files["nodes"])
            + len(self.csv_files["relationships"]),
            "output_directory": str(self.output_dir),
        }
