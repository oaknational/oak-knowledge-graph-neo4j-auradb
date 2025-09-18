#!/usr/bin/env python3
"""
CLI entry point for Oak Knowledge Graph pipeline.
Provides command-line interface for pipeline execution per FUNCTIONAL.md requirements.
"""

import argparse
import sys
import os

from utils.logging import PipelineLogger
from utils.helpers import validate_required_env_vars, format_duration
from pipeline.pipeline import Pipeline, PipelineError, PipelineStage
from pipeline.config_manager import ConfigurationError

import time


def setup_logging(verbose: bool = False) -> PipelineLogger:
    """Setup logging based on environment and verbosity."""
    log_level = os.getenv("LOG_LEVEL", "DEBUG" if verbose else "INFO")
    return PipelineLogger("oak_cli", log_level)


def validate_environment() -> None:
    """Validate required environment variables are set."""
    required_vars = ["HASURA_ENDPOINT", "HASURA_API_KEY", "OAK_AUTH_TYPE"]

    try:
        validate_required_env_vars(required_vars)
    except ValueError as e:
        print(f"Environment validation failed: {e}")
        print("\nRequired environment variables:")
        for var in required_vars:
            print(f"  {var}")
        print("\nSee .env.example for configuration details.")
        sys.exit(1)


def create_pipeline(output_dir: str, verbose: bool = False) -> Pipeline:
    """Create and initialize pipeline with progress reporting."""

    def progress_callback(progress):
        if verbose:
            stage_msg = (
                f"[{progress.stage.value}] {progress.progress_percent:.1f}% - "
                f"{progress.message}"
            )
            print(stage_msg)
            if progress.total_records > 0:
                print(
                    f"  Records: {progress.records_processed}/{progress.total_records}"
                )
        else:
            # Simple progress for non-verbose mode
            print(f"{progress.message}")

    return Pipeline(output_dir=output_dir, progress_callback=progress_callback)


def run_full_pipeline(args) -> int:
    """Execute complete pipeline from config to Neo4j."""
    logger = setup_logging(args.verbose)
    logger.log_pipeline_stage("CLI", "Starting full pipeline execution")

    start_time = time.time()

    try:
        validate_environment()

        pipeline = create_pipeline(args.output_dir, args.verbose)

        # Execute full pipeline
        result = pipeline.run_full_pipeline(
            config_file=args.config,
            use_auradb=args.use_auradb,
            clear_database=args.clear_database,
        )

        execution_time = time.time() - start_time

        print(
            f"\n✅ Pipeline completed successfully in {format_duration(execution_time)}"
        )
        print("📊 Results:")
        node_count = len(result.get("csv_files", {}).get("nodes", []))
        rel_count = len(result.get("csv_files", {}).get("relationships", []))
        print(
            f"  • CSV files: {node_count} node files, {rel_count} "
            f"relationship files"
        )
        print(f"  • Output directory: {args.output_dir}")

        if args.use_auradb and "import_stats" in result:
            stats = result["import_stats"]
            nodes = stats.get("nodes_created", 0)
            rels = stats.get("relationships_created", 0)
            print(f"  • Database import: {nodes} nodes, {rels} relationships")

        return 0

    except (PipelineError, ConfigurationError) as e:
        logger.log_error_with_context("CLI", "Pipeline execution failed", error=e)
        print(f"\n❌ Pipeline failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        return 1
    except Exception as e:
        logger.log_error_with_context("CLI", "Unexpected error", error=e)
        print(f"\n💥 Unexpected error: {e}")
        return 1


def run_extract_only(args) -> int:
    """Extract data only from Hasura API."""
    logger = setup_logging(args.verbose)
    logger.log_pipeline_stage("CLI", "Starting data extraction only")

    try:
        validate_environment()

        pipeline = create_pipeline(args.output_dir, args.verbose)

        # Load config and extract
        pipeline.load_config(args.config)
        extracted_data = pipeline.extract_data()

        print("\n✅ Data extraction completed")
        print(f"📊 Extracted {len(extracted_data)} records")
        print("💾 Pipeline state saved for further processing")

        return 0

    except (PipelineError, ConfigurationError) as e:
        logger.log_error_with_context("CLI", "Data extraction failed", error=e)
        print(f"\n❌ Extraction failed: {e}")
        return 1
    except Exception as e:
        logger.log_error_with_context("CLI", "Unexpected error", error=e)
        print(f"\n💥 Unexpected error: {e}")
        return 1


def run_transform_only(args) -> int:
    """Transform data to CSV format (requires previous extraction)."""
    logger = setup_logging(args.verbose)
    logger.log_pipeline_stage("CLI", "Starting CSV transformation only")

    try:
        pipeline = create_pipeline(args.output_dir, args.verbose)

        # Load config and check for previous data
        pipeline.load_config(args.config)

        if not pipeline.extracted_data:
            print(
                "❌ No extracted data found. Run extraction first with --extract-only"
            )
            return 1

        # Run transformation steps
        pipeline.validate_data()
        pipeline.map_data()
        csv_result = pipeline.transform_to_csv()

        print("\n✅ CSV transformation completed")
        print("📊 Generated:")
        print(f"  • Node files: {len(csv_result.get('nodes', []))}")
        print(f"  • Relationship files: {len(csv_result.get('relationships', []))}")
        print(f"📁 Output directory: {args.output_dir}")

        return 0

    except (PipelineError, ConfigurationError) as e:
        logger.log_error_with_context("CLI", "CSV transformation failed", error=e)
        print(f"\n❌ Transformation failed: {e}")
        return 1
    except Exception as e:
        logger.log_error_with_context("CLI", "Unexpected error", error=e)
        print(f"\n💥 Unexpected error: {e}")
        return 1


def run_load_only(args) -> int:
    """Load CSV files to Neo4j (requires previous transformation)."""
    logger = setup_logging(args.verbose)
    logger.log_pipeline_stage("CLI", "Starting Neo4j load only")

    try:
        pipeline = create_pipeline(args.output_dir, args.verbose)

        # Load config and check for CSV files
        pipeline.load_config(args.config)

        if not pipeline.csv_files.get("nodes") and not pipeline.csv_files.get(
            "relationships"
        ):
            print(
                "❌ No CSV files found. Run transformation first with --transform-only"
            )
            return 1

        # Load to Neo4j
        load_result = pipeline.load_to_neo4j(use_auradb=args.use_auradb)

        print("\n✅ Neo4j load completed")

        if args.use_auradb and "import_stats" in load_result:
            stats = load_result["import_stats"]
            nodes = stats.get("nodes_created", 0)
            rels = stats.get("relationships_created", 0)
            print(f"📊 Database import: {nodes} nodes, {rels} relationships")
        else:
            print("📋 Import commands generated in output directory")

        return 0

    except (PipelineError, ConfigurationError) as e:
        logger.log_error_with_context("CLI", "Neo4j load failed", error=e)
        print(f"\n❌ Load failed: {e}")
        return 1
    except Exception as e:
        logger.log_error_with_context("CLI", "Unexpected error", error=e)
        print(f"\n💥 Unexpected error: {e}")
        return 1


def run_partial_pipeline(args) -> int:
    """Run pipeline with specified stages."""
    logger = setup_logging(args.verbose)
    stages = []

    # Build stage list from arguments
    if args.extract:
        stages.append(PipelineStage.EXTRACTING_DATA)
    if args.validate:
        stages.append(PipelineStage.VALIDATING_DATA)
    if args.map:
        stages.append(PipelineStage.MAPPING_DATA)
    if args.transform:
        stages.append(PipelineStage.TRANSFORMING_CSV)
    if args.load:
        stages.append(PipelineStage.LOADING_NEO4J)

    if not stages:
        print("❌ No pipeline stages specified")
        return 1

    logger.log_pipeline_stage(
        "CLI", f"Starting partial pipeline: {[s.value for s in stages]}"
    )

    try:
        validate_environment()

        pipeline = create_pipeline(args.output_dir, args.verbose)

        # Execute partial pipeline
        pipeline.run_partial_pipeline(
            config_file=args.config,
            stages=stages,
            use_auradb=args.use_auradb,
            clear_database=args.clear_database,
        )

        print("\n✅ Partial pipeline completed")
        print(f"📊 Executed stages: {[s.value for s in stages]}")

        return 0

    except (PipelineError, ConfigurationError) as e:
        logger.log_error_with_context("CLI", "Partial pipeline failed", error=e)
        print(f"\n❌ Pipeline failed: {e}")
        return 1
    except Exception as e:
        logger.log_error_with_context("CLI", "Unexpected error", error=e)
        print(f"\n💥 Unexpected error: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser with all options."""
    parser = argparse.ArgumentParser(
        description="Oak Knowledge Graph Data Pipeline - Extract curriculum "
        "data from Hasura → transform → load to Neo4j",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline execution
  python main.py --config config/oak_curriculum_schema_v0.1.0-alpha.json --full

  # Extract data only
  python main.py --config config/schema.json --extract-only

  # Transform existing data to CSV
  python main.py --config config/schema.json --transform-only

  # Load CSV files to AuraDB
  python main.py --config config/schema.json --load-only --use-auradb

  # Run specific pipeline stages
  python main.py --config config/schema.json --extract --validate --transform

Environment Variables:
  HASURA_ENDPOINT     Hasura GraphQL endpoint URL
  HASURA_API_KEY      Oak authentication key (128 characters)
  OAK_AUTH_TYPE       Set to 'oak-admin' for Oak authentication
  LOG_LEVEL           Logging level (DEBUG, INFO, WARNING, ERROR,
                      CRITICAL)
  LOG_FILE            Optional file path for detailed logging

For more information, see FUNCTIONAL.md and CLAUDE.md
        """,
    )

    # Configuration
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to JSON configuration file (e.g., "
        "config/oak_curriculum_schema_v0.1.0-alpha.json)",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        default="data",
        help="Output directory for CSV files and import commands (default: data)",
    )

    # Execution modes (mutually exclusive)
    execution_group = parser.add_mutually_exclusive_group(required=True)

    execution_group.add_argument(
        "--full",
        action="store_true",
        help="Execute complete pipeline (extract → validate → map → "
        "transform → load)",
    )

    execution_group.add_argument(
        "--extract-only", action="store_true", help="Extract data from Hasura API only"
    )

    execution_group.add_argument(
        "--transform-only",
        action="store_true",
        help="Transform previously extracted data to CSV format",
    )

    execution_group.add_argument(
        "--load-only",
        action="store_true",
        help="Load previously generated CSV files to Neo4j",
    )

    # Individual stage selection for partial pipeline
    parser.add_argument(
        "--extract", action="store_true", help="Extract data from Hasura"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate extracted data"
    )
    parser.add_argument("--map", action="store_true", help="Apply schema mappings")
    parser.add_argument(
        "--transform", action="store_true", help="Transform to CSV format"
    )
    parser.add_argument("--load", action="store_true", help="Load to Neo4j database")

    # Database options
    parser.add_argument(
        "--use-auradb",
        action="store_true",
        help="Use AuraDB direct import instead of generating neo4j-admin commands",
    )

    parser.add_argument(
        "--clear-database",
        action="store_true",
        help="Clear Neo4j database before import (development/testing only)",
    )

    # Output options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with detailed progress reporting",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Oak Knowledge Graph Pipeline v0.1.0-alpha",
    )

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate partial pipeline arguments
    if any([args.extract, args.validate, args.map, args.transform, args.load]):
        return run_partial_pipeline(args)

    # Route to appropriate execution mode
    if args.full:
        return run_full_pipeline(args)
    elif args.extract_only:
        return run_extract_only(args)
    elif args.transform_only:
        return run_transform_only(args)
    elif args.load_only:
        return run_load_only(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
