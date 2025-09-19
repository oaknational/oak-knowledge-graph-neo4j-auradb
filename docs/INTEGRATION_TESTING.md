# Integration Testing Documentation

This document describes the comprehensive integration testing suite for the Oak Knowledge Graph Pipeline, covering end-to-end functionality validation and Neo4j import testing.

## Overview

Task 15 implements complete integration testing to validate that the entire pipeline works correctly with sample data and can successfully generate and import CSV files into Neo4j.

## Test Architecture

### Test Components

1. **Integration Test Suite** (`tests/test_integration.py`)
2. **Test Runner Script** (`scripts/run_integration_tests.sh`)
3. **Neo4j Validation Script** (`scripts/validate_neo4j_import.py`)
4. **Sample Configurations** (`config/integration_test_config.json`)
5. **Mock Data Fixtures** (`tests/fixtures/integration_test_data.json`)

## Test Scenarios

### 1. Configuration Validation Tests

**Purpose**: Verify that integration test configurations load and validate correctly

**Test Cases**:
- ✅ Configuration file parsing
- ✅ Pydantic model validation
- ✅ Environment variable substitution
- ✅ Required field validation
- ✅ Schema mapping completeness

**Expected Results**:
- All configuration files pass Pydantic validation
- Environment variables are correctly substituted
- Invalid configurations fail with clear error messages

### 2. End-to-End Pipeline Tests

**Purpose**: Validate complete pipeline execution with mock data

**Test Cases**:
- ✅ Full pipeline execution with `run_full_pipeline()`
- ✅ Partial pipeline execution with custom stages
- ✅ Progress callback functionality
- ✅ Error handling and recovery
- ✅ Mock Hasura API integration

**Mock Data Scenarios**:
- **Small Dataset**: 2 units, 3 lessons, 3 objectives
- **Empty Dataset**: No records returned
- **Large Dataset**: 100+ records for performance testing
- **Invalid Data**: Malformed records for error handling

**Expected Results**:
- Pipeline executes without errors
- Progress callbacks are triggered correctly
- CSV files are generated in correct format
- Error scenarios are handled gracefully

### 3. CSV Format Validation Tests

**Purpose**: Ensure generated CSV files meet Neo4j import requirements

**Test Cases**:
- ✅ Node CSV header validation (`:ID`, `:LABEL`)
- ✅ Relationship CSV header validation (`:START_ID`, `:END_ID`, `:TYPE`)
- ✅ Type annotation validation (`:string`, `:int`, `:float`, `:boolean`)
- ✅ Data integrity checks
- ✅ ID uniqueness validation
- ✅ Non-null value validation

**Validation Criteria**:
```csv
# Node File Example
:ID,:LABEL,title:string,description:string,order:int
node_001,Unit,"Test Unit","Description",1

# Relationship File Example
:START_ID,:END_ID,:TYPE,order:int
node_001,node_002,CONTAINS,1
```

**Expected Results**:
- All CSV files have correct Neo4j headers
- No null values in required columns
- IDs are unique within node files
- Relationships reference valid node IDs

### 4. Neo4j Import Command Tests

**Purpose**: Verify Neo4j import command generation and format

**Test Cases**:
- ✅ Import command structure validation
- ✅ CSV file path inclusion
- ✅ Database name specification
- ✅ Command syntax correctness

**Expected Command Format**:
```bash
neo4j-admin database import full \
  --nodes=Unit=data/Unit_nodes.csv \
  --relationships=CONTAINS=data/CONTAINS_relationships.csv \
  --overwrite-destination test-db
```

**Expected Results**:
- Commands include all CSV files
- Proper node and relationship mapping
- Valid neo4j-admin syntax

### 5. Data Quality Tests

**Purpose**: Validate data transformation and mapping accuracy

**Test Cases**:
- ✅ Field mapping application
- ✅ Type conversion accuracy
- ✅ ID generation consistency
- ✅ Relationship integrity
- ✅ Data lineage tracking

**Sample Data Transformation**:
```json
// Input (Hasura MV)
{
  "unit_id": "int_test_unit_001",
  "unit_title": "Integration Test Mathematics Unit",
  "duration_minutes": 45
}

// Output (Neo4j CSV)
int_test_unit_001,Unit,"Integration Test Mathematics Unit",45
```

**Expected Results**:
- All source fields are mapped correctly
- Type conversions preserve data integrity
- Generated IDs are consistent across files
- Relationships connect valid nodes

### 6. Error Handling Tests

**Purpose**: Verify robust error handling throughout pipeline

**Test Cases**:
- ✅ Configuration file errors
- ✅ Mock API failures
- ✅ Data validation failures
- ✅ File system errors
- ✅ Recovery and rollback

**Error Scenarios**:
- Invalid JSON configuration
- Missing required fields in mock data
- File permission errors
- Network connection failures
- Invalid data types

**Expected Results**:
- Clear error messages with context
- Graceful failure without corruption
- Proper cleanup of temporary files
- Actionable error descriptions

### 7. Performance Tests

**Purpose**: Validate pipeline performance with larger datasets

**Test Cases**:
- ✅ Large dataset processing (100+ records)
- ✅ Memory usage optimization
- ✅ Batch processing efficiency
- ✅ CSV generation speed

**Performance Benchmarks**:
- 100 records: < 10 seconds
- Memory usage: < 500MB for 1000 records
- CSV generation: < 1MB/second

**Expected Results**:
- Pipeline completes within time limits
- Memory usage remains reasonable
- No performance degradation with scale

## Test Data

### Sample Configuration (`config/integration_test_config.json`)

Simplified configuration for testing with:
- 3 materialized views
- 3 node types (Subject, Unit, Lesson)
- 2 relationship types (BELONGS_TO, CONTAINS)
- Test limit of 10 records
- Database clearing enabled

### Mock Data (`tests/fixtures/integration_test_data.json`)

Realistic curriculum data including:
- **Subjects**: Mathematics, Science
- **Units**: 2 units with proper hierarchical structure
- **Lessons**: 3 lessons with proper ordering
- **Objectives**: 3 learning objectives linked to lessons

## Running Integration Tests

### Automated Test Suite

```bash
# Run complete integration test suite
./scripts/run_integration_tests.sh

# Run specific pytest tests
pytest tests/test_integration.py -v

# Run with coverage reporting
pytest tests/test_integration.py --cov=pipeline --cov-report=html
```

### Manual Validation Steps

1. **Generate Test Data**:
```bash
python main.py --config config/integration_test_config.json --full
```

2. **Validate CSV Files**:
```bash
# Check generated files
ls -la data/*.csv

# Validate headers
head -1 data/*_nodes.csv
head -1 data/*_relationships.csv
```

3. **Test Neo4j Import** (requires Neo4j credentials):
```bash
# Set environment variables
export NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"

# Run validation script
python scripts/validate_neo4j_import.py data/ config/integration_test_config.json
```

## Quality Gates

All integration tests must pass the following criteria:

### ✅ Test Execution
- All pytest tests pass (100% success rate)
- No unhandled exceptions during pipeline execution
- Progress reporting functions correctly

### ✅ Data Quality
- CSV files generated for all configured node/relationship types
- All CSV files have correct Neo4j headers
- No data corruption during transformation
- ID consistency across node and relationship files

### ✅ Format Compliance
- Node files include `:ID` and `:LABEL` columns
- Relationship files include `:START_ID`, `:END_ID`, `:TYPE` columns
- Proper type annotations in headers
- Valid Neo4j import command generation

### ✅ Error Handling
- Graceful handling of configuration errors
- Clear error messages with context
- Proper cleanup on failure
- No silent failures

## Integration with CLAUDE.md Standards

This integration testing suite complies with all requirements from `CLAUDE.md`:

- **Testing Standards**: pytest framework, comprehensive coverage
- **Error Handling**: Fail-fast with clear messages
- **CSV Requirements**: Neo4j compliance with proper headers
- **Quality Gates**: Manual CSV import validation included
- **Architecture**: Uses Strategy + Factory patterns
- **Configuration**: JSON-based with environment variable support

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Run `pip install -r requirements.txt`
2. **Permission Errors**: Ensure scripts have execute permissions (`chmod +x`)
3. **Neo4j Connection**: Verify environment variables are set correctly
4. **File Not Found**: Run tests from project root directory

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export LOG_FILE=integration_test.log
./scripts/run_integration_tests.sh
```

## Next Steps

After integration testing completion:

1. **Task 16**: Code quality validation
2. **Task 17**: Documentation completion
3. **Task 18**: Final validation and production readiness

The integration test suite provides confidence that the Oak Knowledge Graph Pipeline is ready for production deployment and can handle real curriculum data from Oak's Hasura instance.