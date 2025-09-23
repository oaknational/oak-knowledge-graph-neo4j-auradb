#!/usr/bin/env python3
"""
Simple batch job entry point for Oak Knowledge Graph.
Executes the complete pipeline with a single command.
"""

import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from config_manager import ConfigManager, ConfigurationError
from hasura_extractor import HasuraExtractor
from data_cleaner import DataCleaner
from schema_mapper import SchemaMapper


def setup_logging():
    """Setup console logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler()],
    )


def validate_environment():
    """Validate required environment variables are set."""
    required_vars = ["HASURA_ENDPOINT", "HASURA_API_KEY", "OAK_AUTH_TYPE"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   {var}")
        print("\nPlease check your .env file or environment configuration.")
        print("See .env.example for required variables.")
        sys.exit(1)


# Configuration file to use - change this to switch config files
DEFAULT_CONFIG_FILE = "oak_curriculum_schema_v0.1.0-alpha.json"


def find_config_file():
    """Find the configuration file to use."""
    config_dir = Path("config")

    # Use the default config file if it exists
    preferred_path = config_dir / DEFAULT_CONFIG_FILE

    if preferred_path.exists():
        print(f"📋 Using configuration file: {DEFAULT_CONFIG_FILE}")
        return DEFAULT_CONFIG_FILE

    # Fallback to other config files
    config_files = list(config_dir.glob("*.json"))

    if not config_files:
        print("❌ No configuration files found in config/ directory")
        sys.exit(1)

    # Use the first config file found
    config_file = config_files[0].name
    print(f"📋 Using configuration file: {config_file}")
    return config_file


def main():
    """Main batch job execution."""
    print("🚀 Oak Knowledge Graph Batch Job")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Validate environment
    validate_environment()

    try:
        # Find and load configuration
        config_file = find_config_file()
        config_manager = ConfigManager()
        config = config_manager.load_config(config_file)

        output_dir = Path("data")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check what to run based on config
        export_from_hasura = config.get("export_from_hasura", True)
        import_to_neo4j = config.get("import_to_neo4j", True)

        logger.info(f"Export from Hasura: {export_from_hasura}")
        logger.info(f"Import to Neo4j: {import_to_neo4j}")

        # Hasura Export: Extract and clean data from Hasura
        cleaned_csv_file = None
        if export_from_hasura:
            print("🔄 Hasura Export: Extracting and cleaning data from Hasura...")

            # Clear ALL existing files before Hasura Export
            import glob

            existing_files = glob.glob(str(output_dir / "*"))
            for file_path in existing_files:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            if existing_files:
                logger.info(f"Cleared {len(existing_files)} existing files")

            # Extract data
            extractor = HasuraExtractor(
                endpoint=config["hasura_endpoint"], output_dir=str(output_dir)
            )

            csv_file = extractor.extract_and_join(
                materialized_views=config["materialized_views"],
                join_strategy=config["join_strategy"],
                test_limit=config.get("test_limit"),
            )

            # Always clean data
            cleaner = DataCleaner(output_dir=str(output_dir), filters=config.get("filters"))
            cleaned_csv_file = cleaner.clean_data(csv_file)

            print(f"✅ Hasura Export completed: {cleaned_csv_file}")

        # Neo4j Import: Map schema and import to Neo4j
        if import_to_neo4j:
            print("🔄 Neo4j Import: Mapping schema and importing to Neo4j...")

            # Clear Neo4j CSV files before Neo4j Import (preserve Hasura Export outputs)
            import glob

            neo4j_files = glob.glob(str(output_dir / "*nodes*.csv")) + glob.glob(
                str(output_dir / "*relationships*.csv")
            )
            for file_path in neo4j_files:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            if neo4j_files:
                logger.info(f"Cleared {len(neo4j_files)} existing Neo4j CSV files")

            # Find input file for Neo4j Import
            if not cleaned_csv_file:
                # Look for previous Hasura Export
                possible_files = list(output_dir.glob("*cleaned*.csv")) or list(
                    output_dir.glob("*.csv")
                )
                if not possible_files:
                    raise Exception(
                        "No CSV file found for import. Run export_from_hasura first."
                    )
                cleaned_csv_file = str(possible_files[0])
                logger.info(f"Using existing CSV file: {cleaned_csv_file}")

            # Map to Neo4j schema
            mapper = SchemaMapper()
            csv_files = mapper.map_from_csv(
                csv_file=cleaned_csv_file,
                schema_mapping=config["schema_mapping"],
                output_dir=str(output_dir),
            )

            # Import to Neo4j
            from pipeline.auradb_loader import AuraDBLoader

            clear_database = config.get("clear_database_before_import", False)
            schema_mapping = config.get("schema_mapping", {})
            loader = AuraDBLoader(clear_before_import=clear_database, schema_config=schema_mapping)

            node_files = csv_files.get("node_files", [])
            rel_files = csv_files.get("relationship_files", [])

            import_stats = loader.execute_import(node_files, rel_files)

            if import_stats.get("success", False):
                queries = import_stats.get("queries_executed", 0)
                print(f"✅ Neo4j Import completed: {queries} queries executed")
            else:
                errors = import_stats.get("errors", ["Unknown error"])
                raise Exception(f"Neo4j import failed: {'; '.join(errors)}")

        print("✅ Batch job completed successfully!")
        print("📊 Check the data/ directory for output files")

    except (ConfigurationError, Exception) as e:
        logger.error(f"Batch job failed: {e}")
        print(f"❌ Batch job failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Batch job interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
