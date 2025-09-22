# Functional Specification

## Project Summary
Simple batch job to extract Oak Curriculum data from specified Hasura materialized views, join into a single CSV, apply optional data cleaning, and import into Neo4j knowledge graph.

## Core Requirements

### 1. Data Extraction & Consolidation
- Connect to Hasura GraphQL API using configurable endpoint
- Query specified materialized views based on JSON configuration
- Join all MV data into a single consolidated CSV file
- Handle authentication and rate limiting
- **Success Criteria:** All specified MVs extracted and joined without data loss

### 2. Data Cleaning & Preprocessing
- Optional preprocessing area in code for data cleaning operations
- Apply transformations to consolidated CSV before schema mapping
- Save cleaned CSV for inspection/debugging
- **Success Criteria:** Clean, validated data ready for knowledge graph import

### 3. Schema Mapping System
- JSON-based configuration for CSV field mappings to Neo4j knowledge graph
- Support for node and relationship definitions
- Field transformation rules (rename, type conversion, computed fields)
- **Success Criteria:** Successful mapping from CSV to knowledge graph schema

### 4. Knowledge Graph Import
- Import cleaned and mapped data directly into Neo4j knowledge graph
- Validate successful import with proper relationships
- **Success Criteria:** Complete knowledge graph populated without errors

### 5. Configuration Management
- Load schema mappings from JSON files
- Simple validation of required configuration keys
- **Success Criteria:** Easy maintenance of mappings when schema changes

## User Interface Requirements

### Batch Job Interface
```bash
# Simple batch execution
python main.py
```

**Features:**
- Single command execution with selective phases via config flags
- Progress logging to console with descriptive phase names
- Error reporting with clear messages
- Final status summary

## Data Flow Requirements

**Hasura Export** (if `export_from_hasura: true`):
1. **Configuration Loading:** Parse JSON schema mappings
2. **Data Extraction:** Fetch data from specified Hasura MVs and join into single CSV
3. **Data Cleaning:** Apply preprocessing transformations to cleaned CSV

**Neo4j Import** (if `import_to_neo4j: true`):
4. **Schema Mapping:** Apply CSV field mappings to knowledge graph schema
5. **Knowledge Graph Import:** Import directly into Neo4j knowledge graph

## Error Handling Requirements

- **Validation Errors:** Clear messages for invalid configurations
- **API Errors:** Handle Hasura connection and query failures
- **Data Errors:** Identify and report malformed data records
- **File Errors:** Handle CSV generation and file system issues
- **User Feedback:** Show progress and errors via console logging

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
- [x] Extract data from specified Hasura MVs and join into single CSV
- [x] Optional data cleaning/preprocessing area
- [x] Map CSV fields to knowledge graph schema via JSON configuration
- [x] Direct import into Neo4j knowledge graph
- [x] Simple batch job execution

### Success Metrics
- Single command executes selected phases via config flags without intervention
- Data successfully exported from Hasura and/or imported into Neo4j knowledge graph
- Phase execution controlled by simple boolean flags in single JSON config
- Error messages provide actionable guidance
- Simple, maintainable direct component usage architecture