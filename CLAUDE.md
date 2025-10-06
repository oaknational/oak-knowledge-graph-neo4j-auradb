# CLAUDE.md - Development Standards

## Quick Setup
```bash
pip install -r requirements.txt
python main.py  # Run batch job
```

## Code Standards

### Style (Enforced)
- **Format:** `black .` (no exceptions)
- **Lint:** `flake8` (must pass) - configured for 88-char line length in `.flake8`
- **Naming:** `snake_case` functions/vars, `PascalCase` classes
- **Docstrings:** Minimal, only where code intent unclear

### Architecture (Required)
- **Pattern:** Simple batch job processing with direct component usage
- **Components:** ConfigManager, HasuraExtractor, DataCleaner, SchemaMapper, AuraDBLoader
- **Data:** Plain Python dictionaries for configuration and data
- **Structure:** Single main.py entry point with direct component instantiation
- **Environment:** Python 3.10+ required for Neo4j driver routing compatibility

### Dependencies (Locked)
```txt
pandas>=1.5.0      # CSV operations
requests>=2.28.0   # API calls
black>=22.0.0      # Code formatting
flake8>=5.0.0      # Linting
pytest>=7.0.0      # Unit testing
neo4j>=5.0.0       # Database driver
python-dotenv>=1.0.0  # Environment management
```

## Development Rules

### Error Handling
- **Strategy:** Fail fast with clear messages
- **Pattern:** Simple try/catch, no retries
- **Logging:** Console output, optional file logging
- **Validation:** Pydantic models catch data issues early
- **Context:** Always include relevant identifiers (view names, field names) in error messages

### Oak Authentication (Required)
- **Headers:** `x-oak-auth-key` + `x-oak-auth-type: oak-admin`
- **Environment:** `HASURA_API_KEY`, `OAK_AUTH_TYPE`, `HASURA_ENDPOINT`
- **No Standard Auth:** Do not use `x-hasura-admin-secret` or JWT Bearer tokens

### Logging Configuration (Optional)
- **Environment:** `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR, CRITICAL), `LOG_FILE` (file path for optional file logging)
- **Default:** Console logging at INFO level, file logging disabled

### Testing Requirements
- **Scope:** Unit tests for pipeline classes + integration tests for end-to-end validation
- **Framework:** pytest
- **Coverage:** Core transformation logic + complete pipeline execution
- **Mocking:** Hasura API responses in fixtures + environment variable mocking
- **Standards:** 100% test pass rate required, comprehensive edge case coverage
- **Fixtures:** Use `tests/fixtures/` for mock data, realistic curriculum examples
- **Integration:** `scripts/run_integration_tests.sh` for automated validation

### File Organization
```
pipeline/     # Core classes
models/       # Pydantic schemas
utils/        # Shared helpers
config/       # JSON mappings
tests/        # Unit tests + integration tests
scripts/      # Test runners + validation tools
docs/         # Testing documentation
```

### Configuration
- **Format:** JSON files in `/config` with SemVer versioning
- **Validation:** Pydantic models enforce schema
- **Security:** Environment variables for credentials
- **Active Schema:** `oak_curriculum_schema_v0.1.0-alpha.json`
- **Versioning:** Professional SemVer 2.0.0 with MVP pre-release strategy

## Commit Standards
- **Format:** Conventional commits
- **Examples:**
  - `feat: add schema mapper class`
  - `fix: csv header generation`
  - `docs: update setup instructions`

## Critical Implementation Notes

### Data Flow (Mandatory)
**Hasura Export Phase** (if `export_from_hasura: true`):
1. **Clear ALL Files** → ensures fresh import every time
2. **HasuraExtractor** queries specified MVs with explicit fields → JOIN strategy (NO concatenation)
3. **DataCleaner** preprocessing → cleaned CSV

**Neo4j Import Phase** (if `import_to_neo4j: true`):
4. **Clear Neo4j CSV Files** → preserves Hasura export outputs
5. **SchemaMapper** deduplication + transformations → node/relationship CSVs
6. **AuraDBLoader** imports using CSV `:TYPE` column → production database ready

### CSV Requirements (Neo4j Compliance)
- **Node files:** Use `property:ID(NodeType)` format (e.g., `slug:ID(Subject)`)
- **Relationship files:** Use `:START_ID(NodeType)`, `:END_ID(NodeType)`, `:TYPE`
- **Types:** Use `:string`, `:int`, `:float`, `:boolean` in headers based on config
- **No UUIDs:** Use actual Hasura field values as unique identifiers

### Configuration Structure (JSON with Type-Safe Field Specification)
```json
{
  "materialized_views": {
    "view_name": ["field1", "field2", "field3"]
  },
  "join_strategy": {
    "type": "single_source|multi_source_join",
    "primary_mv": "primary_view_name",
    "joins": [{
      "mv": "joined_view_name",
      "join_type": "left|inner|right|outer",
      "on": {
        "left_key": "column_name|[\"col1\", \"col2\"]",
        "right_key": "column_name|[\"col1\", \"col2\"]"
      }
    }]
  },
  "schema_mapping": {
    "nodes": {
      "NodeType": {
        "id_field": {
          "hasura_col": "column_name",
          "type": "string|int|float|boolean",
          "property_name": "neo4j_property_name",
          "expand_list": false
        },
        "properties": {
          "property_name": {
            "hasura_col": "column_name",
            "type": "string|int|float|boolean|list"
          }
        }
      }
    },
    "relationships": {
      "config_key": {
        "relationship_type": "NEO4J_TYPE",
        "start_node_type": "NodeType",
        "start_csv_field": "csv_column_name",
        "end_node_type": "NodeType",
        "end_csv_field": "csv_column_name",
        "properties": {
          "property_name": {
            "hasura_col": "column_name",
            "type": "string|int|float|boolean"
          }
        }
      }
    }
  }
}
```

**Critical Requirements:**
- `export_from_hasura`/`import_to_neo4j`: Boolean flags for phase control
- `materialized_views`: Dict format with explicit field lists
- `join_strategy`: Optional multi-source joins with pandas merge strategies
  - Supports composite keys: `"left_key": ["col1", "col2"]` for multi-column joins
  - Auto-explodes list-type join keys (e.g., `programme_slug_by_year`) before merging
- `id_field`: Must specify `hasura_col`, `type`, and `property_name`
- **Neo4j Naming**: Use initial capital + lowercase (e.g., `Unitvariant`)
- **Type Safety**: All fields require explicit type specification including `list` for arrays
- **Collection Types**: `list` for native Neo4j arrays with JSON string elements for complex objects
- **Array Expansion**: Optional `expand_list: true` creates separate nodes from array items
- **Relationship Fields**: `start_csv_field`/`end_csv_field` reference CSV column names (supports expandable arrays)
- **Empty Value Handling**: Empty strings, arrays, and objects automatically omitted from Neo4j
- **Unicode Support**: Escape sequences automatically decoded to proper characters
- **Hasura Array Fields**: Fields returned as arrays are automatically exploded if used as join keys

### Batch Job Interface
- **Entry Point:** `main.py` in root with direct component usage
- **Configuration:** Single JSON file `oak_curriculum_schema_v0.1.0-alpha.json`
- **Environment Loading:** Must call `load_dotenv()` to read `.env` file
- **Execution:** `python main.py` runs phases based on boolean config flags

### Array Expansion (Optional Feature)
- **Purpose:** Create separate nodes from array fields instead of storing as lists
- **Configuration:** Set `expand_list: true` in node `id_field` config
- **Mechanism:** Uses `property_name` to extract ID from each array object
- **Relationships:** Automatically expands when referencing expandable array fields
- **Use Case:** Thread nodes from `threads` array with individual Unit → Thread relationships

## Quality Gates (Must Pass)
1. `black --check .`
2. `flake8`
3. `pytest tests/`
4. Manual validation: Neo4j knowledge graph import successful

### Performance Standards
- **Database Operations:** UNWIND batch queries (1,000 records/batch) for optimal Neo4j performance
- **File Splitting:** Automatic chunking at 10,000 rows to prevent timeout issues
- **Memory:** Use `pandas.read_csv(low_memory=False)` for large CSV processing
- **Scalability:** Production-tested with 18,238+ curriculum records
- **Error Prevention:** Suppress DtypeWarnings with proper memory settings

## Reference Files
- **Functional requirements:** FUNCTIONAL.md
- **Architecture details:** ARCHITECTURE.md
- **Active configuration:** `config/oak_curriculum_schema_v0.1.0-alpha.json` (main.py references -alpha.json, but -alpha-2.json contains latest updates)
- **Version history:** `config/config_versions.md`