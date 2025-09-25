# Project Development History

## Project Overview
Oak Knowledge Graph Data Pipeline - Extract curriculum data from Hasura materialized views → transform to Neo4j CSV format → bulk import to Neo4j AuraDB.

## Specifications Created
- **FUNCTIONAL.md**: Complete functional requirements and acceptance criteria
- **ARCHITECTURE.md**: Technical architecture, design patterns, file structure
- **CLAUDE.md**: Compact development standards and quality gates
- **TO-DO.md**: 18 sequential tasks organized into 6 phases with dependencies

## Key Architectural Decisions
- **Language**: Python 3.8+ (leverages existing codebase)
- **Patterns**: Strategy + Factory for extensibility, Class-based pipeline
- **Dependencies**: pandas, requests, pydantic, streamlit, black, flake8, pytest
- **Structure**: pipeline/, models/, utils/, config/, tests/, data/ (gitignored)
- **UI**: Single-page Streamlit interface for local deployment only
- **Testing**: Unit tests only for MVP, pytest framework

## Completed Tasks

### ✅ Task 1: Environment Setup (Phase 1)
**Implementation Details:**
- Created root `requirements.txt` with locked dependencies from CLAUDE.md
- Built complete directory structure per ARCHITECTURE.md:
  ```
  pipeline/    # Core classes with __init__.py
  models/      # Pydantic schemas with __init__.py
  utils/       # Shared helpers with __init__.py
  config/      # JSON mappings
  data/        # Generated CSVs (gitignored)
  tests/       # Unit tests with __init__.py and fixtures/
  ```
- Enhanced `.gitignore` to explicitly ignore `data/` directory and `*.csv` files

**Quality Gates:** ✅ `pip install -r requirements.txt` works, structure matches ARCHITECTURE.md

### ✅ Task 2: Pydantic Data Models (Phase 1)
**Implementation Details:**
- Created `models/config.py`: FieldMapping, NodeMapping, RelationshipMapping, PipelineConfig
- Created `models/hasura.py`: HasuraResponse, MaterializedViewResponse for API validation
- Created `models/neo4j.py`: Neo4jNode/Relationship, ImportNode/Relationship, ImportCommand
- Added RelationshipMapping class (not in original ARCHITECTURE.md spec) with type, start/end node fields

**Quality Gates:** ✅ All models pass `black --check` and `flake8`, imports work correctly

### ✅ Task 3: Configuration Management (Phase 1)
**Implementation Details:**
- Created `pipeline/config_manager.py`: ConfigManager class with JSON loading/validation
- Created `config/schema_template.json`: Example configuration with curriculum nodes/relationships
- Created `.env.example`: Environment variable documentation for credentials
- Environment variable substitution: `${VAR_NAME}` placeholders in JSON automatically replaced
- Error handling: Clear validation messages with field paths and actionable descriptions

**Quality Gates:** ✅ Passes `black` and `flake8`, loads/validates configs correctly

### ✅ Task 4: Base Strategy Classes (Phase 2)
**Implementation Details:**
- Created `pipeline/extractors.py`: ExtractionStrategy abstract base class + ExtractorFactory
- Created `pipeline/transformers.py`: TransformationStrategy and RelationshipTransformationStrategy abstract classes + TransformerFactory
- Factory pattern implementation with strategy registration, creation, and discovery methods
- Added RelationshipTransformationStrategy (enhancement) to handle relationship mappings separately from nodes

**Quality Gates:** ✅ Passes `black --check` and `flake8`, all imports successful

### ✅ Task 5: Hasura Extractor (Phase 2)
**Implementation Details:**
- Implemented `HasuraExtractor` class in `pipeline/extractors.py` with full GraphQL API client
- **Oak Authentication**: Uses custom `x-oak-auth-key` + `x-oak-auth-type: oak-admin` headers (discovered from TypeScript reference)
- **Real Data Connection**: Successfully tested with Oak curriculum materialized views (6/6 accessible)
- **Query Generation**: Dynamic GraphQL queries with proper naming (e.g., `GetCurriculumUnits`)
- **Error Handling**: Comprehensive coverage for API, GraphQL, authentication, and network failures
- **Strategy Integration**: Auto-registered with ExtractorFactory as "hasura" strategy
- **Testing**: 18 unit tests with mock fixtures, updated for Oak authentication
- **Environment Variables**: `HASURA_API_KEY`, `OAK_AUTH_TYPE`, `HASURA_ENDPOINT`

**Quality Gates:** ✅ 18/18 tests pass, flake8 clean, black formatted, real data extraction confirmed

**Key Features:**
- Production-ready connection to Oak Hasura instance
- Verified access to all 6 required materialized views
- Clean authentication implementation (no legacy auth code)
- End-to-end data extraction validated

### ✅ Task 6: Data Validator (Phase 2)
**Implementation Details:**
- Created `pipeline/validators.py`: DataValidator class with ValidationResult container
- **Batch Validation**: Configurable batch size (default 100) for performance with large datasets
- **Comprehensive Validation Methods**:
  - `validate_hasura_response()` - Validates Hasura GraphQL API responses against models
  - `validate_materialized_view_data()` - Batch validates MV records with error context
  - `validate_node_data()` - Validates against NodeMapping requirements (ID field, properties)
  - `validate_relationship_data()` - Validates against RelationshipMapping requirements
  - `validate_batch()` - Generic validation for any Pydantic model
- **Detailed Error Reporting**: Actionable messages with field paths, record indices, validation types
- **Performance Features**: Batch processing, configurable sizes, memory-efficient validation

**Quality Gates:** ✅ Passes `black --check` and `flake8`, uses modern `model_validate()` method

**Key Features:**
- Validates data quality before transformation step
- Fail-fast validation with clear error context (view names, record indices, field names)
- Supports all data types in pipeline (Hasura responses, nodes, relationships)

### ✅ Task 7: Schema Mapper (Phase 2)
**Implementation Details:**
- Created `pipeline/mappers.py`: SchemaMapper class with field mapping and transformation logic
- **Field Transformation Engine**: 6+ transformation types (uppercase, lowercase, strip, prefix, suffix, custom)
- **Node ID Generation**: UUID-based unique IDs for relationships with consistency guarantees
- **Data Lineage Tracking**: Complete audit trail via DataLineage class for all transformations and ID mappings
- **Type Conversion**: Robust string, int, float, boolean conversions with error handling
- **Comprehensive Testing**: 15 unit tests with 100% pass rate covering all functionality

**Quality Gates:** ✅ All tests pass, black formatted, ready for CSVTransformer integration

**Key Features:**
- Applies JSON configuration mappings to transform Hasura MV data
- Generates throwaway UUIDs for Neo4j import (removed after import as per CLAUDE.md)
- Maintains field transformation audit trail for debugging and validation
- Handles large datasets efficiently with pandas DataFrame operations

### ✅ Task 8: CSV Transformer (Phase 2)
**Implementation Details:**
- Created `CSVTransformer` class in `pipeline/transformers.py` with full Neo4j CSV generation
- **Neo4j Compliance**: Node files with `:ID/:LABEL`, relationship files with `:START_ID/:END_ID/:TYPE`
- **Type Annotations**: Proper headers (`:string`, `:int`, `:float`, `:boolean`) based on configuration mappings
- **CSV Optimization**: QUOTE_ALL quoting, UTF-8 encoding, optimized for Neo4j bulk import performance
- **Validation & QA**: `validate_csv_format()` and `generate_import_summary()` methods
- **Strategy Integration**: Auto-registered with TransformerFactory, follows established patterns

**Quality Gates:** ✅ Functional testing passed, generates valid Neo4j CSV files, black formatted

### ✅ Task 9: Neo4j Loader (Phase 2)
**Implementation Details:**
- Created `Neo4jLoader` class in `pipeline/loaders.py` with CSV validation and command generation
- Created `AuraDBLoader` class in `pipeline/auradb_loader.py` for direct cloud database operations
- **High-Performance Import**: UNWIND batch queries (1000 records/batch) for production scalability
- **Database Management**: Configurable clearing with `clear_database_before_import` setting
- **Comprehensive Statistics**: Node/relationship counts, execution summaries, error reporting
- **Professional Configuration**: SemVer 2.0.0 versioning system with MVP pre-release strategy
- **Production Database Testing**: Successfully tested with actual AuraDB instance, end-to-end validation
- **Python 3.10 Requirement**: Discovered and documented Neo4j driver routing compatibility requirement

**Quality Gates:** ✅ Real database testing passed, UNWIND batch import validated, codebase cleanup completed

**Key Features:**
- Two loader strategies: CSV command generation and direct database execution
- Professional schema versioning with `oak_curriculum_schema_v0.1.0-alpha.json`
- Database utilities in organized `utils/database_utils.py` structure
- Configurable database clearing for development/testing workflows
- Production-ready performance for thousands of records

**Architecture Decisions:**
- Switched from individual CREATE statements to UNWIND batches for performance
- Added configurable database clearing functionality to PipelineConfig
- Established professional versioning system in `config/config_versions.md`
- Created conda environment specification with Python 3.10 requirement

**Codebase Cleanup:**
- Removed all test/debug scripts and experimental files
- Kept essential unit tests in `tests/` directory for production quality assurance
- Cleaned config directory, removing outdated templates
- Maintained professional file organization with only production components

### ✅ Task 10: Main Pipeline Class (Phase 3)
**Implementation Details:**
- Created `pipeline/pipeline.py`: Pipeline class with complete orchestration of 6-stage data flow
- **Component Orchestration**: Manages entire pipeline per CLAUDE.md requirements (ConfigManager → HasuraExtractor → DataValidator → SchemaMapper → CSVTransformer → Neo4jLoader/AuraDBLoader)
- **Dependency Injection**: All pipeline components properly injected using Strategy + Factory patterns
- **Progress Reporting**: PipelineProgress dataclass with callback system, 7 distinct stages, real-time feedback
- **Error Recovery**: PipelineError class with fail-fast strategy, stage context, actionable error messages
- **Execution Methods**: `run_full_pipeline()`, `run_partial_pipeline()`, individual stage methods, state tracking

**Quality Gates:** ✅ Passes black/flake8, integration tested, error handling verified, progress reporting validated

**Key Features:**
- Complete end-to-end pipeline orchestration with flexible execution (full/partial)
- Production-ready with both Neo4j admin commands and direct AuraDB imports
- Comprehensive state management and data lineage tracking
- Stage-specific error handling with debugging context

### ✅ Task 11: Logging and Utilities (Phase 3)
**Implementation Details:**
- Created `utils/logging.py`: PipelineLogger class with console and optional file logging
- Created `utils/helpers.py`: 13 shared utility functions for pipeline operations
- **Environment Integration**: `LOG_LEVEL` and `LOG_FILE` environment variables
- **Key Functions**: `validate_required_env_vars()`, `format_duration()`, `load_json_with_env_substitution()`

**Quality Gates:** ✅ Passes black/flake8, production-ready logging infrastructure

### ✅ Task 12: CLI Interface (Phase 4)
**Implementation Details:**
- Created `main.py`: Complete CLI entry point with argparse
- **Execution Modes**: `--full`, `--extract-only`, `--transform-only`, `--load-only`
- **Partial Pipeline**: `--extract --validate --map --transform --load` for custom stage combinations
- **Database Options**: `--use-auradb`, `--clear-database` flags
- **Progress Reporting**: Verbose and non-verbose modes with emoji status indicators
- **Error Handling**: Comprehensive environment validation, pipeline error context, fail-fast strategy
- **Help System**: Complete documentation with examples and environment variables

**Quality Gates:** ✅ Passes black/flake8, comprehensive CLI supporting all FUNCTIONAL.md requirements

**Key Features:**
- Complete CLI interface per FUNCTIONAL.md specifications
- Environment validation for Oak authentication (HASURA_ENDPOINT, HASURA_API_KEY, OAK_AUTH_TYPE)
- Progress callbacks with execution time reporting
- Flexible pipeline execution (full, partial, individual stages)

### ✅ Task 13: Streamlit Web Interface (Phase 4)
**Implementation Details:**
- Created `streamlit_app.py`: Single-page web interface with three-section layout (Config → Preview → Execute)
- **Configuration Editor**: JSON editor with real-time Pydantic validation, "Load Default Config" button, syntax highlighting
- **Data Preview**: Configuration summary metrics, materialized view listing, environment variable status dashboard
- **Pipeline Execution**: Full/partial pipeline controls, AuraDB/CSV options, real-time progress indicators with callbacks
- **Results Display**: Execution summaries, generated file listings, import commands, comprehensive error handling
- **Environment Integration**: Automatic `.env` loading via `python-dotenv`, Oak authentication validation
- **Bug Fixes**: Fixed ConfigManager validation (no `load_from_dict` method), improved environment variable error messaging

**Quality Gates:** ✅ Passes black/flake8, production-ready single-page interface supporting all FUNCTIONAL.md requirements

**Key Features:**
- Complete web interface per CLAUDE.md specifications (Config → Preview → Execute layout)
- Smart environment variable detection with helpful warnings instead of hard errors
- Real-time configuration validation with detailed error messages including field paths
- Integrated pipeline orchestration with progress callbacks and execution time reporting
- Professional UI/UX with responsive layout, status indicators, and comprehensive help text

### ✅ Task 14: Unit Tests (Phase 5)
**Implementation Details:**
- Created `tests/test_config_manager.py`: 13 tests for ConfigManager class with environment variable substitution, JSON validation, and error handling
- Created `tests/test_transformers.py`: 32 tests for CSVTransformer with Neo4j compliance, type annotations, CSV validation, and factory patterns
- Created `tests/test_pipeline.py`: 32 tests for Pipeline orchestration with component integration, progress reporting, and error recovery
- Enhanced `tests/fixtures/`: Added validation test data, invalid data scenarios, and comprehensive test configurations
- **Quality Gates Achieved**: 110/110 tests passing, black formatting compliance, flake8 linting clean
- **Test Coverage**: Core transformation logic, pipeline orchestration, comprehensive edge cases, mock API scenarios

**Quality Gates:** ✅ All CLAUDE.md standards met - pytest framework, 100% pass rate, comprehensive coverage

**Key Features:**
- Comprehensive unit test suite with realistic curriculum examples
- Mock Hasura API responses with Oak authentication patterns
- Strategy pattern testing with factory registration validation
- Pipeline component integration testing with dependency injection
- Error handling validation with fail-fast behavior verification

### ✅ Task 15: Integration Testing (Phase 5)
**Implementation Details:**
- Created `config/integration_test_config.json`: Simplified test configuration for 3 MVs, 3 node types, 2 relationship types
- Created `tests/fixtures/integration_test_data.json`: Realistic curriculum data with 2 subjects, 2 units, 3 lessons, 3 objectives
- Created `tests/test_integration.py`: End-to-end pipeline testing with mock data, CSV validation, Neo4j compliance checks
- Created `scripts/run_integration_tests.sh`: Automated test runner with CSV format validation
- Created `scripts/validate_neo4j_import.py`: Real database import validation script
- Created `docs/INTEGRATION_TESTING.md`: Comprehensive testing documentation with 7 scenario categories

**Quality Gates:** ✅ Configuration validation, data extraction (8 records), component integration, CSV format compliance

**Key Features:**
- End-to-end pipeline execution with mock Hasura data
- Neo4j CSV format validation (`:ID`, `:LABEL`, `:START_ID`, `:END_ID`, `:TYPE` headers)
- Real database import validation tools
- Comprehensive test scenarios: configuration, extraction, validation, CSV generation, error handling
- Production-ready integration test infrastructure

**Technical Achievement:** Pipeline successfully extracts data and demonstrates component integration readiness

### ✅ Post-Task 15: Production Pipeline Refinements (NEW)
**Implementation Details:**
- **Simplified Architecture Transition**: Moved from complex strategy pattern to simple batch job architecture per user request
- **Direct Pipeline Components**: BatchProcessor, ConfigManager, HasuraExtractor, DataCleaner, SchemaMapper, Neo4jLoader
- **Field Reading Fix**: Resolved Hasura field extraction issue - script now reads all configured fields (24 fields) instead of just 2
- **Configuration Evolution**: Changed from list to dict format for materialized_views with explicit field specification
- **JOIN Strategy Implementation**: Completely removed concatenation logic, implemented JOIN-only data consolidation
- **Deduplication System**: Added comprehensive deduplication for both nodes and relationships using `seen_ids` tracking
- **Directory Clearing**: Added automatic output directory clearing at pipeline start for fresh imports
- **Schema Mapper Enhancement**: Added `relationship_type` field support for multiple config entries creating same Neo4j relationship type
- **AuraDB Loader Fix**: Fixed critical bug where relationship types were extracted from filenames instead of CSV `:TYPE` column

**Key Technical Achievements:**
- **200 Records Processing**: Successfully extracts 200 records with 25 columns from `published_mv_lesson_openapi_1_2_3`
- **Multi-Node Generation**: Creates Year (11), Subject (20), and UnitVariant (96) nodes with proper deduplication
- **Unified Relationship Types**: Both Year→UnitVariant and Subject→UnitVariant relationships correctly use "HAS_UNIT" type in Neo4j
- **Production Data Flow**: Hasura → CSV → Clean → Map → Neo4j with full pipeline validation

**Quality Gates:** ✅ All tests pass, production data validated, Neo4j import successful with correct relationship types

### ✅ Task 16: Simplified Config-Driven Architecture (September 2024)
**Implementation Details:**
- **Removed Complex BatchProcessor**: Eliminated unnecessary `batch_processor.py` orchestration layer
- **Direct Component Usage**: Simplified `main.py` to directly use ConfigManager, HasuraExtractor, DataCleaner, SchemaMapper, AuraDBLoader
- **Single Config File**: Removed duplicate configs, using only `oak_curriculum_schema_v0.1.0-alpha.json`
- **Simple Boolean Flags**: `export_from_hasura` and `import_to_neo4j` replace complex stage configuration
- **Smart File Management**: Hasura Export clears all files, Neo4j Import preserves Hasura outputs
- **Descriptive Naming**: "Stage 1/Stage 2" renamed to "Hasura Export/Neo4j Import"
- **Fixed Relationship Types**: Corrected to use `:TYPE` column instead of filename extraction

**Quality Gates:** ✅ All complexity removed, direct component usage, single config file, clear naming

**Key Features:**
- Simple `python main.py` execution with config-driven behavior
- Two-phase pipeline: Hasura Export → Neo4j Import
- Selective execution via boolean flags in single JSON config
- Proper relationship type handling using CSV `:TYPE` column

### ✅ Task 17: Complete Node and Relationship CSV Generation (September 2024)
**Implementation Details:**
- **Config-Driven Node Generation**: Updated schema_mapper.py to use `id_field` with `property_name` and `type` from config
- **Neo4j ID Format**: Nodes use `property:ID(NodeType)` format (e.g., `slug:ID(Subject)`, `unitVariantId:ID(Unitvariant)`)
- **No UUID Generation**: Removed all UUID code, using actual Hasura field values as unique identifiers
- **Type-Safe Property Mapping**: Dynamic property mapping from config with proper type annotations
- **Deduplication**: Based on ID field values only, each unique ID gets one node
- **Relationship CSV Format**: Uses `:START_ID(NodeType)` and `:END_ID(NodeType)` headers with type specifications

**Quality Gates:** ✅ Node CSVs generated with correct format, relationships created successfully in Neo4j

**Key Features:**
- Node CSV format: `slug:ID(Subject),title:string` with data like `"science","Science"`
- Relationship CSV format: `:START_ID(Subject),:END_ID(Unitvariant),:TYPE,order:int`
- Config-driven property names and types (no hardcoded values)
- Neo4j naming convention: `Unitvariant` (not `UnitVariant`)

### ✅ Task 18: Neo4j AuraDB Import with Type-Safe Conversion (September 2024)
**Implementation Details:**
- **Config-Driven Type Conversion**: AuraDBLoader reads ID field types from config for proper data conversion
- **Dynamic Property Name Resolution**: `_get_id_property_name()` and `_get_id_field_type()` methods extract from schema config
- **Batch Processing**: 1000-row batches using UNWIND queries for high performance
- **Type-Safe Relationships**: Converts CSV values to correct types (string/int/float) based on config before matching
- **Cypher Query Generation**: `MATCH (start:Subject {slug: row.start_id}) MATCH (end:Unitvariant {unitVariantId: row.end_id})`

**Quality Gates:** ✅ 27 nodes and 48 relationships successfully created in Neo4j, type conversion works correctly

**Technical Achievement:** Fixed critical type mismatch bug where CSV "104.0" (string) wasn't matching node property 104.0 (float)

## Session 2: Full-Scale Production Deployment (Sept 25, 2025)

### Critical Production Issues Resolved

#### 1. HAS_UNITVARIANT Relationships Not Created
**Problem**: Despite successful processing logs, no HAS_UNITVARIANT relationships appeared in Neo4j due to property name mismatches between CSV data (snake_case) and existing Neo4j nodes (camelCase).

**Root Cause**: Relationship config used Neo4j property names (`unitSlug`, `programmeSlug`) but CSV contained Hasura column names (`unit_slug`, `programme_slug`).

**Solution**:
- Updated relationship config to use Hasura column names for CSV data reading
- Enhanced AuraDBLoader to translate to Neo4j property names for node matching
- Added missing Unit and Programme node definitions to schema config

**Result**: 9,060 HAS_UNITVARIANT relationships successfully created

#### 2. Massive Data Expansion Performance Issue (36 rows → 2.78M rows)
**Problem**: Script timeout due to JSON array unpacking creating massive data expansion in DataCleaner.

**Solution**: Implemented just-in-time array expansion strategy:
- Removed hardcoded array unpacking from DataCleaner
- Added dynamic array expansion in SchemaMapper only when needed
- Made array expansion config-driven via `array_expansion` parameter

#### 3. Large CSV File Import Timeouts (50K+ rows)
**Problem**: Neo4j import failing on large CSV files.

**Solution**: Implemented automatic file splitting:
- Split large CSVs into 10,000-row chunks in AuraDBLoader
- Fixed node label extraction bug for split files
- Added DtypeWarning suppression with `low_memory=False`

#### 4. Config Clarity and Consistency Issues
**Problem**: Confusing mixed naming conventions in relationship configuration.

**Solution**: Implemented unified field mapping (Option 3):
- Renamed `start_node_field` → `start_csv_field`
- Renamed `end_node_field` → `end_csv_field`
- All relationship fields now consistently reference CSV column names
- AuraDBLoader automatically maps to Neo4j property names

### Production Scale Results
- **Records Processed**: 18,238 curriculum records
- **Nodes Created**: 2,053 Unitvariant + 12,473 Lesson nodes
- **Relationships Created**: 15,218 HAS_LESSON + 9,060 HAS_UNITVARIANT relationships
- **Performance**: ~1,000 records per batch via UNWIND queries
- **File Management**: Automatic chunking prevents timeout issues

### Configuration Pattern Established
```json
"relationships": {
  "unit_has_unitvariant": {
    "start_csv_field": "unit_slug",        // CSV column (Hasura)
    "end_csv_field": "unitVariantSlug",    // CSV column (synthetic)
    "start_node_type": "Unit",             // Neo4j label
    "end_node_type": "Unitvariant"         // Neo4j label
  }
}
```

### Data Flow Optimization
1. **Hasura Export**: Extract → Clean (no array expansion) → CSV
2. **Schema Mapping**: Just-in-time array expansion → Node/relationship CSVs
3. **Neo4j Import**: File splitting → Batch UNWIND queries → Database

### Technical Standards Established
- Consistent use of pandas `low_memory=False` for large CSV processing
- UNWIND batch queries (1,000 records) for optimal Neo4j performance
- Proper type conversion based on schema config field types
- CSV field references always point to actual data columns
- Synthetic field generation follows Neo4j naming conventions

## Current State (Sept 25, 2025)
**Status**: Production-ready full-scale curriculum data pipeline
**Database**: 9,060 HAS_UNITVARIANT relationships successfully imported
**Config**: `oak_curriculum_schema_v0.1.0-alpha-2.json` (upgraded to -alpha-3)
**Performance**: Optimized for large dataset processing without timeouts

### Active Configuration
- **Export Phase**: `export_from_hasura: false` (skip Hasura extraction)
- **Import Phase**: `import_to_neo4j: true` (run Neo4j import only)
- **Array Expansion**: All disabled for performance
- **Database Clearing**: Disabled to preserve existing data
- **File Splitting**: Automatic chunking at 10,000 rows

### Environment Status
- **Hasura**: `HASURA_ENDPOINT`, `HASURA_API_KEY`, `OAK_AUTH_TYPE=oak-admin`
- **Neo4j**: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- **Database**: Production-ready with thousands of nodes and relationships

### Established Patterns
- **Property Name Mapping**: CSV generation uses source names, Neo4j import translates to target names
- **Relationship Configuration**: `start_csv_field`/`end_csv_field` reference actual CSV columns
- **Synthetic Fields**: Added to cleaned CSV with Neo4j naming convention (camelCase)
- **File Organization**: Auto-split files use `{original_name}_part{N}.csv` pattern
- **Error Handling**: Fail fast with clear error messages including identifiers