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
from batch_processor import BatchProcessor, BatchProcessorError


def setup_logging():
    """Setup console logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler()]
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
    print("🚀 Oak Knowledge Graph Batch Processor")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Validate environment
    validate_environment()

    try:
        # Find configuration file
        config_file = find_config_file()

        # Initialize and run batch processor
        processor = BatchProcessor(output_dir="data")

        # Check if we should skip data cleaning
        skip_cleaning = os.getenv("SKIP_DATA_CLEANING", "").lower() in ("true", "1", "yes")

        if skip_cleaning:
            print("⚠️  Data cleaning will be skipped (SKIP_DATA_CLEANING=true)")

        # Execute the batch processing pipeline
        processor.process(
            config_file=config_file,
            skip_cleaning=skip_cleaning
        )

        print("✅ Batch processing completed successfully!")
        print("📊 Check the data/ directory for output files")
        print("🎯 Knowledge graph has been updated in Neo4j")

    except BatchProcessorError as e:
        logger.error(f"Batch processing failed: {e}")
        print(f"❌ Batch processing failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Batch processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()