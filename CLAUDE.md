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
- **Node files:** Must include `:ID` column and `:LABEL`
- **Relationship files:** Must include `:START_ID`, `:END_ID`, `:TYPE`
- **Types:** Use `:string`, `:int`, `:float`, `:boolean` in headers
- **IDs:** Generate unique throwaway IDs for import, remove after

### Configuration Structure (JSON with Field Specification)
```json
{
  "materialized_views": {
    "view_name": ["field1", "field2", "field3"]
  },
  "join_strategy": {
    "type": "single_source" | "multi_source_join",
    "primary_mv": "view_name",
    "joins": []
  },
  "schema_mapping": {
    "relationships": {
      "config_key": {
        "relationship_type": "NEO4J_TYPE",
        "start_node_field": "field_name",
        "end_node_field": "field_name"
      }
    }
  }
}
```

**Critical Requirements:**
- `export_from_hasura`: Boolean flag to control Hasura Export phase
- `import_to_neo4j`: Boolean flag to control Neo4j Import phase
- `materialized_views`: Dict format with explicit field lists (NOT list format)
- `join_strategy`: Required for data consolidation strategy
- `relationship_type`: Allows multiple configs to create same Neo4j relationship type

### Batch Job Interface
- **Entry Point:** `main.py` in root with direct component usage
- **Configuration:** Single JSON file `oak_curriculum_schema_v0.1.0-alpha.json`
- **Environment Loading:** Must call `load_dotenv()` to read `.env` file
- **Execution:** `python main.py` runs phases based on boolean config flags

## Quality Gates (Must Pass)
1. `black --check .`
2. `flake8`
3. `pytest tests/`
4. Manual validation: Neo4j knowledge graph import successful

### Performance Standards
- **Database Operations:** Efficient bulk import operations
- **Scalability:** Production-ready for thousands of curriculum records
- **Memory:** Efficient CSV processing for large datasets

## Reference Files
- **Functional requirements:** FUNCTIONAL.md
- **Architecture details:** ARCHITECTURE.md
- **Active configuration:** `config/oak_curriculum_schema_v0.1.0-alpha.json`
- **Version history:** `config/config_versions.md`