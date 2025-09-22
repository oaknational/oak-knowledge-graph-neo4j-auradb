import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from config_manager import ConfigManager, ConfigurationError
from hasura_extractor import HasuraExtractor
from data_cleaner import DataCleaner
from schema_mapper import SchemaMapper
from neo4j_loader import Neo4jLoader


class BatchProcessorError(Exception):
    """Exception raised when batch processing fails."""
    pass


class BatchProcessor:
    """
    Simple linear batch processor for Oak Knowledge Graph.

    Executes the complete pipeline in order:
    1. Load configuration
    2. Extract data from Hasura MVs and join into single CSV
    3. Optional data cleaning/preprocessing
    4. Map CSV fields to knowledge graph schema
    5. Import directly into Neo4j knowledge graph
    """

    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.config_manager = ConfigManager()
        self.config: Optional[Dict[str, Any]] = None

    def process(self, config_file: str, skip_cleaning: bool = False) -> None:
        """
        Execute the complete batch processing pipeline.

        Args:
            config_file: Path to JSON configuration file
            skip_cleaning: Whether to skip the data cleaning step
        """
        self.logger.info("="*60)
        self.logger.info("Starting Oak Knowledge Graph Batch Processing")
        self.logger.info("="*60)

        try:
            # Step 0: Clear output directory for fresh import
            self._clear_output_directory()

            # Step 1: Load Configuration
            self._load_configuration(config_file)

            # Step 2: Extract and Join Data
            csv_file = self._extract_and_join_data()

            # Step 3: Optional Data Cleaning
            cleaned_csv_file = self._clean_data(csv_file, skip_cleaning)

            # Step 4: Map to Knowledge Graph Schema and Generate CSV Files
            csv_files = self._map_schema(cleaned_csv_file)

            # Step 5: Import CSV Files to Neo4j Knowledge Graph
            self._import_to_neo4j(csv_files)

            self.logger.info("="*60)
            self.logger.info("Batch processing completed successfully!")
            self.logger.info("="*60)

        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise BatchProcessorError(f"Pipeline failed: {e}") from e

    def _load_configuration(self, config_file: str) -> None:
        """Step 1: Load and validate configuration."""
        self.logger.info("Step 1: Loading configuration...")

        try:
            self.config = self.config_manager.load_config(config_file)

            # Log configuration summary
            mvs = self.config.get('materialized_views', [])
            self.logger.info(f"Configuration loaded: {len(mvs)} materialized views configured")
            self.logger.info(f"Materialized views: {', '.join(mvs)}")

        except ConfigurationError as e:
            raise BatchProcessorError(f"Configuration loading failed: {e}")

    def _extract_and_join_data(self) -> str:
        """Step 2: Extract data from Hasura MVs and join into single CSV."""
        self.logger.info("Step 2: Extracting and joining data...")

        try:
            extractor = HasuraExtractor(
                endpoint=self.config['hasura_endpoint'],
                output_dir=str(self.output_dir)
            )

            materialized_views = self.config['materialized_views']
            test_limit = self.config.get('test_limit')

            csv_file = extractor.extract_and_join(
                materialized_views=materialized_views,
                join_strategy=self.config['join_strategy'],
                test_limit=test_limit
            )

            self.logger.info(f"Data extraction completed: {csv_file}")
            return csv_file

        except Exception as e:
            raise BatchProcessorError(f"Data extraction failed: {e}")

    def _clean_data(self, csv_file: str, skip_cleaning: bool) -> str:
        """Step 3: Optional data cleaning and preprocessing."""
        if skip_cleaning:
            self.logger.info("Step 3: Skipping data cleaning (as requested)")
            return csv_file

        self.logger.info("Step 3: Cleaning and preprocessing data...")

        try:
            cleaner = DataCleaner(output_dir=str(self.output_dir))
            cleaned_csv_file = cleaner.clean_data(csv_file)

            self.logger.info(f"Data cleaning completed: {cleaned_csv_file}")
            return cleaned_csv_file

        except Exception as e:
            raise BatchProcessorError(f"Data cleaning failed: {e}")

    def _map_schema(self, csv_file: str) -> Dict[str, List[str]]:
        """Step 4: Map CSV fields to knowledge graph schema and generate Neo4j CSV files."""
        self.logger.info("Step 4: Mapping CSV to knowledge graph schema...")

        try:
            mapper = SchemaMapper()
            schema_mapping = self.config['schema_mapping']

            csv_files = mapper.map_from_csv(
                csv_file=csv_file,
                schema_mapping=schema_mapping,
                output_dir=str(self.output_dir)
            )

            # Log mapping summary
            node_files = csv_files.get('node_files', [])
            rel_files = csv_files.get('relationship_files', [])
            self.logger.info(f"Schema mapping completed: {len(node_files)} node CSV files, {len(rel_files)} relationship CSV files")

            return csv_files

        except Exception as e:
            raise BatchProcessorError(f"Schema mapping failed: {e}")

    def _import_to_neo4j(self, csv_files: Dict[str, List[str]]) -> None:
        """Step 5: Import CSV files to Neo4j knowledge graph using existing AuraDB loader."""
        self.logger.info("Step 5: Importing CSV files to Neo4j knowledge graph...")

        try:
            # Use the existing working AuraDBLoader
            from pipeline.auradb_loader import AuraDBLoader

            # Get optional configuration
            clear_database = self.config.get('clear_database_before_import', False)

            loader = AuraDBLoader(clear_before_import=clear_database)

            node_files = csv_files.get('node_files', [])
            rel_files = csv_files.get('relationship_files', [])

            # Execute the import using the working pattern
            import_stats = loader.execute_import(node_files, rel_files)

            # Log import summary
            self.logger.info(f"Neo4j import completed:")
            self.logger.info(f"  Success: {import_stats.get('success', False)}")
            self.logger.info(f"  Queries executed: {import_stats.get('queries_executed', 0)}")
            self.logger.info(f"  Database cleared: {import_stats.get('database_cleared', False)}")

            if not import_stats.get('success', False):
                errors = import_stats.get('errors', ['Unknown error'])
                raise Exception(f"Import failed: {'; '.join(errors)}")

        except Exception as e:
            raise BatchProcessorError(f"Neo4j import failed: {e}")

    def _clear_output_directory(self) -> None:
        """Step 0: Clear output directory for fresh import."""
        self.logger.info("Step 0: Clearing output directory for fresh import...")

        try:
            import glob
            import os

            # Remove all existing files from output directory
            existing_files = glob.glob(str(self.output_dir / "*"))
            for file_path in existing_files:
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        self.logger.debug(f"Removed existing file: {file_path}")
                    except OSError as e:
                        self.logger.warning(f"Could not remove {file_path}: {e}")

            if existing_files:
                self.logger.info(f"Cleared {len(existing_files)} existing files from {self.output_dir} for fresh import")
            else:
                self.logger.info("Output directory was already empty")

        except Exception as e:
            raise BatchProcessorError(f"Failed to clear output directory: {e}")