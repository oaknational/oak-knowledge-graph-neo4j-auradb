# Architecture Specification

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | Neo4j driver routing compatibility, excellent data processing libraries |
| Data Processing | pandas | Efficient CSV manipulation and data transformation |
| API Client | requests | Simple HTTP client for Hasura GraphQL calls |
| Configuration | JSON + Python dict | Simple configuration loading and basic validation |
| Package Manager | pip + requirements.txt | Simple, widely supported, minimal overhead |
| Code Quality | Black + flake8 | Standard Python formatting and linting |
| Testing | pytest | Industry standard, simple unit testing |
| Database Driver | neo4j>=5.0.0 | Official Neo4j Python driver for AuraDB |
| Environment | python-dotenv | Secure credential management |

## System Architecture

### Design Pattern
- **Simple Batch Processing:** Linear execution flow with clear separation of concerns

### Core Components

```
BatchProcessor (Main orchestrator)
├── ConfigManager (JSON configuration handling)
├── HasuraExtractor (GraphQL API client)
├── DataCleaner (Optional preprocessing area)
├── SchemaMapper (CSV to knowledge graph mapping)
└── Neo4jLoader (Direct knowledge graph import)
```

### Component Responsibilities

#### BatchProcessor
- Orchestrates entire data flow in simple linear sequence
- Manages component execution order
- Handles error reporting and logging
- Provides progress feedback to console

#### ConfigManager
- Loads JSON schema mappings
- Provides configuration as Python dictionaries
- Basic validation of required configuration keys

#### HasuraExtractor
- Connects to Oak Hasura GraphQL endpoint
- Uses Oak authentication (x-oak-auth-key + x-oak-auth-type)
- Queries specified materialized views
- Joins all MV data into single consolidated CSV
- Saves raw extracted data for inspection

#### DataCleaner
- Provides optional preprocessing area in code
- Applies data cleaning transformations to consolidated CSV
- Re-saves cleaned CSV for inspection/debugging
- User can add custom cleaning logic as needed

#### SchemaMapper
- Maps CSV fields to Neo4j knowledge graph schema
- Applies transformations per JSON configuration
- Handles node and relationship mappings
- Prepares data for knowledge graph import

#### Neo4jLoader
- Imports mapped data directly into Neo4j knowledge graph
- Handles node and relationship creation
- Provides import statistics and validation
- Production-ready for large datasets

## Data Flow Architecture

```
JSON Config → ConfigManager → Configuration Loaded
                ↓
Hasura MVs → HasuraExtractor → Consolidated CSV
                ↓
Raw CSV → DataCleaner → Cleaned CSV (Optional)
                ↓
Cleaned CSV + Config → SchemaMapper → Mapped Data
                ↓
Mapped Data → Neo4jLoader → Knowledge Graph Import
```

## File Structure

```
/
├── main.py                 # Batch job entry point
├── batch_processor.py      # Main BatchProcessor class
├── config_manager.py       # Configuration handling
├── hasura_extractor.py     # Hasura data extraction
├── data_cleaner.py         # Optional data preprocessing
├── schema_mapper.py        # CSV to knowledge graph mapping
├── neo4j_loader.py         # Knowledge graph import
├── models/
│   ├── __init__.py
│   ├── config.py           # Configuration Pydantic models
│   └── data.py             # Data models
├── config/                 # JSON schema mapping files
│   └── schema_mapping.json # CSV field to knowledge graph mapping
├── data/                   # Generated CSV files (gitignored)
├── tests/
│   ├── __init__.py
│   ├── test_batch_processor.py
│   ├── test_extractors.py
│   └── fixtures/           # Test data
└── requirements.txt
```

## Interface Contracts

### Configuration Schema (Simple JSON)
```python
# Example configuration structure
config = {
    "hasura_endpoint": "https://api.example.com/v1/graphql",
    "materialized_views": ["curriculum_mv", "lessons_mv"],
    "schema_mapping": {
        "nodes": {
            "Curriculum": {
                "id_field": "curriculum_id",
                "properties": {
                    "title": "curriculum_title",
                    "subject": "subject_name"
                }
            }
        },
        "relationships": {
            "HAS_LESSON": {
                "start_node_field": "curriculum_id",
                "end_node_field": "lesson_id",
                "properties": {}
            }
        }
    }
}

# Simple loading function
def load_config(config_path):
    with open(config_path) as f:
        return json.load(f)
```

## Error Handling Strategy

### Error Categories
1. **Configuration Errors:** Invalid JSON, missing fields, type mismatches
2. **API Errors:** Network failures, authentication, rate limiting
3. **Data Errors:** Validation failures, missing required fields
4. **File System Errors:** Permission issues, disk space, file corruption

### Error Handling Approach
- **Fail Fast:** Validate configuration and connectivity before processing
- **Clear Messages:** Provide actionable error descriptions with context
- **Console Logging:** Show errors and progress via console output
- **Graceful Exit:** Stop processing on critical errors with clear status

## Performance Considerations

### Memory Management
- Stream large datasets using pandas chunking
- Process CSV files in configurable batch sizes
- Clear intermediate data structures after processing

### I/O Optimization
- Minimize Hasura API calls using efficient GraphQL queries
- Write CSV files directly without intermediate storage
- Use efficient pandas operations for data transformation

### Scalability
- Support parallel processing of independent data sets
- Configurable batch sizes for different deployment environments
- Efficient memory usage for datasets up to 100K records

## Security Architecture

### Data Protection
- No sensitive data logged or persisted
- Environment variables for API credentials
- Input validation for all external data sources

### Configuration Security
- JSON schema validation prevents injection attacks
- File system access limited to designated directories
- No code execution from configuration files

## Deployment Architecture

### Local Development
- Single-machine deployment only
- No external dependencies beyond Python packages
- Streamlit runs on localhost:8501
- Data files stored locally in `/data` directory

### Configuration Management
- Environment-specific configuration via JSON files
- No hardcoded credentials or endpoints
- Version-controlled schema mappings

## Testing Strategy

### Unit Testing Scope
- Configuration loading and validation
- Data transformation logic
- CSV generation and formatting
- Error handling scenarios

### Integration Testing Scope (Added)
- End-to-end pipeline execution with mock data
- CSV format validation for Neo4j compliance
- Component integration and orchestration
- Real database import validation tools

### Test Data Management
- Sample Hasura responses in `/tests/fixtures`
- Integration test data with realistic curriculum examples
- Mock API responses for reliable testing
- Environment variable mocking for testing

### Testing Infrastructure
- Simple unit tests for each component
- Integration tests for end-to-end batch processing
- Mock data for reliable testing