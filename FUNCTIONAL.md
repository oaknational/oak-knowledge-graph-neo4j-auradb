# Functional Specification

## Project Summary
Extract Oak Curriculum data from Hasura materialized views and transform it into Neo4j knowledge graph via bulk CSV import.

## Core Requirements

### 1. Data Extraction
- Connect to Hasura GraphQL API using configurable endpoint
- Query specified materialized views based on JSON configuration
- Support optional row limiting for testing purposes (test_limit parameter)
- Handle authentication and rate limiting
- Export raw data to intermediate CSV format
- **Success Criteria:** All configured MVs extracted without data loss

### 2. Schema Mapping System
- JSON-based configuration for field mappings (Hasura MV → Neo4j properties)
- Support for node and relationship definitions
- Field transformation rules (rename, type conversion, computed fields)
- Validation of mapping configuration against available MV fields
- **Success Criteria:** Easy maintenance of mappings when MVs or graph schema change

### 3. Data Transformation
- Convert Hasura data to Neo4j bulk import CSV format
- Generate unique node IDs for relationship references
- Apply proper Neo4j type annotations (`:ID`, `:string`, `:int`, etc.)
- Split data into separate node and relationship CSV files
- **Success Criteria:** Valid Neo4j import CSVs with correct headers and data types

### 4. Neo4j Preparation
- Generate neo4j-admin import command with all CSV files
- Validate CSV format meets Neo4j bulk import requirements
- Provide import statistics and file summaries
- **Success Criteria:** Successful Neo4j database import without errors

### 5. Configuration Management
- Load/save schema mappings from JSON files
- Validate configuration against Pydantic schemas
- Support multiple mapping configurations for different data sets
- Optional test_limit parameter for development/testing with small data samples
- **Success Criteria:** Non-technical users can edit mappings via JSON files

## User Interface Requirements

### CLI Interface
```bash
# Full pipeline execution
python main.py --config config/curriculum.json --extract --transform --load

# Individual steps
python main.py --config config/curriculum.json --extract-only
python main.py --config config/curriculum.json --transform-only
```

### Streamlit Web Interface (Local Only)
- **Schema Mapping Editor:** JSON editor with syntax validation
- **Data Preview:** Show sample transformations before execution
- **Pipeline Controls:** Start/stop buttons with progress indicators
- **Results Viewer:** Display generated CSV files and import commands
- **Error Display:** Show validation errors and execution logs

## Data Flow Requirements

1. **Configuration Loading:** Parse JSON schema mappings
2. **Data Extraction:** Fetch data from configured Hasura MVs
3. **Data Validation:** Validate against Pydantic models
4. **Field Mapping:** Apply transformations per schema configuration
5. **CSV Generation:** Create Neo4j-compatible import files
6. **Import Preparation:** Generate neo4j-admin commands

## Error Handling Requirements

- **Validation Errors:** Clear messages for invalid configurations
- **API Errors:** Retry logic for transient Hasura failures
- **Data Errors:** Identify and report malformed data records
- **File Errors:** Handle CSV generation and file system issues
- **User Feedback:** Show progress and errors in both CLI and web interface

## Performance Requirements

- Process datasets up to 100,000 records efficiently
- Generate CSV files suitable for Neo4j bulk import performance
- Provide progress feedback for long-running operations
- Memory-efficient processing for large datasets

## Quality Requirements

- **Data Integrity:** No data loss during transformation
- **Reproducibility:** Same input always produces same output
- **Maintainability:** Easy to modify schema mappings
- **Usability:** Clear error messages and documentation
- **Reliability:** Graceful handling of common failure scenarios

## Security Requirements

- No hardcoded credentials in code or configuration files
- Environment variables for sensitive configuration
- Input validation for all external data
- Safe handling of API responses

## Acceptance Criteria

### Minimum Viable Product
- [ ] Extract data from at least one Hasura MV
- [ ] Transform to valid Neo4j CSV format
- [ ] Generate working neo4j-admin import command
- [ ] Basic Streamlit interface for schema editing
- [ ] JSON configuration validation

### Success Metrics
- Pipeline completes without manual intervention
- Generated CSV imports successfully into Neo4j
- Schema mappings can be modified by non-developers
- Error messages provide actionable guidance
- Documentation sufficient for handoff to development team