# Architecture Specification

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.8+ | Existing codebase, excellent data processing libraries |
| Data Processing | pandas | Efficient CSV manipulation and data transformation |
| API Client | requests | Simple HTTP client for Hasura GraphQL calls |
| Data Validation | Pydantic | Type safety, automatic validation, JSON schema generation |
| Web Interface | Streamlit | Rapid development, Python-native, local deployment |
| Package Manager | pip + requirements.txt | Simple, widely supported, minimal overhead |
| Code Quality | Black + flake8 | Standard Python formatting and linting |
| Testing | pytest | Industry standard, simple unit testing |

## System Architecture

### Design Patterns
- **Strategy Pattern:** Pluggable extraction and transformation strategies
- **Factory Pattern:** Component creation based on configuration
- **Class-based Pipeline:** Clear separation of concerns with dependency injection

### Core Components

```
Pipeline (Orchestrator)
├── ConfigManager (JSON configuration handling)
├── HasuraExtractor (GraphQL API client)
├── SchemaMapper (Field mapping logic)
├── DataValidator (Pydantic model validation)
├── CSVTransformer (Neo4j format conversion)
└── Neo4jLoader (Import file generation)
```

### Component Responsibilities

#### Pipeline
- Orchestrates entire data flow
- Manages component dependencies
- Handles high-level error recovery
- Provides progress reporting interface

#### ConfigManager
- Loads/validates JSON schema mappings
- Manages configuration file discovery
- Provides typed configuration objects
- Validates mapping completeness

#### HasuraExtractor
- Connects to Hasura GraphQL endpoint
- Executes parameterized queries based on config
- Handles authentication and retries
- Returns structured data for validation

#### SchemaMapper
- Applies field transformations per JSON config
- Handles type conversions and computed fields
- Manages node ID generation for relationships
- Provides data lineage tracking

#### DataValidator
- Validates extracted data against Pydantic models
- Ensures data quality before transformation
- Provides detailed validation error reports
- Supports batch validation for performance

#### CSVTransformer
- Converts validated data to Neo4j CSV format
- Generates proper type headers (`:ID`, `:string`, etc.)
- Splits data into node and relationship files
- Optimizes CSV structure for bulk import performance

#### Neo4jLoader
- Generates neo4j-admin import commands
- Validates CSV format requirements
- Provides import statistics and validation
- Creates import directory structure

## Data Flow Architecture

```
JSON Config → ConfigManager → Strategy Selection
                ↓
Hasura MV → HasuraExtractor → Raw Data
                ↓
Raw Data → DataValidator → Validated Data
                ↓
Validated Data + Config → SchemaMapper → Mapped Data
                ↓
Mapped Data → CSVTransformer → Neo4j CSVs
                ↓
Neo4j CSVs → Neo4jLoader → Import Commands
```

## File Structure

```
/
├── main.py                 # CLI entry point
├── streamlit_app.py        # Web interface (single-page)
├── pipeline/
│   ├── __init__.py
│   ├── pipeline.py         # Main Pipeline class
│   ├── config_manager.py   # Configuration handling
│   ├── extractors.py       # HasuraExtractor + Strategy base
│   ├── mappers.py          # SchemaMapper implementation
│   ├── transformers.py     # CSVTransformer + Strategy base
│   ├── loaders.py          # Neo4jLoader implementation
│   └── validators.py       # DataValidator + Pydantic models
├── models/
│   ├── __init__.py
│   ├── config.py           # Configuration Pydantic models
│   ├── hasura.py           # Hasura response models
│   └── neo4j.py            # Neo4j data models
├── utils/
│   ├── __init__.py
│   ├── logging.py          # Logging configuration
│   └── helpers.py          # Shared utility functions
├── config/                 # JSON schema mapping files
│   ├── curriculum_nodes.json
│   ├── lesson_relationships.json
│   └── schema_template.json
├── data/                   # Generated CSV files (gitignored)
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_extractors.py
│   ├── test_transformers.py
│   └── fixtures/           # Test data
└── requirements.txt
```

## Interface Contracts

### Configuration Schema (Pydantic Models)
```python
class NodeMapping(BaseModel):
    label: str
    id_field: str
    properties: Dict[str, FieldMapping]

class FieldMapping(BaseModel):
    source_field: str
    target_type: str
    transformation: Optional[str]

class PipelineConfig(BaseModel):
    hasura_endpoint: str
    materialized_views: List[str]
    node_mappings: List[NodeMapping]
    relationship_mappings: List[RelationshipMapping]
```

### Strategy Interfaces
```python
class ExtractionStrategy(ABC):
    @abstractmethod
    def extract(self, config: HasuraConfig) -> List[Dict]

class TransformationStrategy(ABC):
    @abstractmethod
    def transform(self, data: List[Dict], mapping: NodeMapping) -> DataFrame
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
- **Graceful Degradation:** Continue processing when possible, report issues
- **User Feedback:** Show errors in both CLI and Streamlit interfaces

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

### Test Data Management
- Sample Hasura responses in `/tests/fixtures`
- Expected CSV outputs for regression testing
- Mock API responses for reliable testing

### Testing Exclusions (MVP)
- Integration testing with live Hasura/Neo4j
- Performance testing with large datasets
- End-to-end UI testing