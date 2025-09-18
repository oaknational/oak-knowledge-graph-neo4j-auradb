# CLAUDE.md - Development Standards

## Quick Setup
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py  # Web interface
python main.py --help           # CLI interface
```

## Code Standards

### Style (Enforced)
- **Format:** `black .` (no exceptions)
- **Lint:** `flake8` (must pass)
- **Naming:** `snake_case` functions/vars, `PascalCase` classes
- **Docstrings:** Minimal, only where code intent unclear

### Architecture (Required)
- **Patterns:** Strategy + Factory for extractors/transformers
- **Classes:** Pipeline, ConfigManager, HasuraExtractor, SchemaMapper, CSVTransformer, Neo4jLoader, DataValidator
- **Models:** Pydantic for all data validation and configuration
- **Structure:** See ARCHITECTURE.md file structure

### Dependencies (Locked)
```txt
pandas>=1.5.0      # CSV operations
requests>=2.28.0   # API calls
pydantic>=1.10.0   # Data validation
streamlit>=1.25.0  # Web interface
black>=22.0.0      # Code formatting
flake8>=5.0.0      # Linting
pytest>=7.0.0      # Unit testing
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

### Testing Requirements
- **Scope:** Unit tests for pipeline classes only
- **Framework:** pytest
- **Coverage:** Core transformation logic
- **Mocking:** Hasura API responses in fixtures
- **Standards:** 100% test pass rate required, comprehensive edge case coverage
- **Fixtures:** Use `tests/fixtures/` for mock data, realistic curriculum examples

### File Organization
```
pipeline/     # Core classes
models/       # Pydantic schemas
utils/        # Shared helpers
config/       # JSON mappings
tests/        # Unit tests only
```

### Configuration
- **Format:** JSON files in `/config`
- **Validation:** Pydantic models enforce schema
- **Security:** Environment variables for credentials
- **Example:** See `config/schema_template.json`

## Commit Standards
- **Format:** Conventional commits
- **Examples:**
  - `feat: add schema mapper class`
  - `fix: csv header generation`
  - `docs: update setup instructions`

## Critical Implementation Notes

### Data Flow (Mandatory)
1. ConfigManager loads JSON → validates with Pydantic
2. HasuraExtractor queries Oak API → returns raw dict data
3. DataValidator applies Pydantic models → validates structure
4. SchemaMapper applies config transformations → mapped data
5. CSVTransformer generates Neo4j format → typed CSV files
6. Neo4jLoader creates import commands → ready for neo4j-admin

### CSV Requirements (Neo4j Compliance)
- **Node files:** Must include `:ID` column and `:LABEL`
- **Relationship files:** Must include `:START_ID`, `:END_ID`, `:TYPE`
- **Types:** Use `:string`, `:int`, `:float`, `:boolean` in headers
- **IDs:** Generate unique throwaway IDs for import, remove after

### Pydantic Models (Required Structure)
```python
# Config models in models/config.py
class FieldMapping(BaseModel):
    source_field: str
    target_type: str
    transformation: Optional[str] = None

class NodeMapping(BaseModel):
    label: str
    id_field: str
    properties: Dict[str, FieldMapping]

# Data models in models/hasura.py and models/neo4j.py
# IMPORTANT: Use model_validate() not deprecated parse_obj()
```

### Streamlit Interface (Single Page)
- **Layout:** Config editor (top) → Preview (middle) → Execute (bottom)
- **No tabs:** Everything on one page for simplicity
- **File:** `streamlit_app.py` in root
- **Local only:** No deployment configuration needed

## Quality Gates (Must Pass)
1. `black --check .`
2. `flake8`
3. `pytest tests/`
4. Manual validation: sample CSV imports into Neo4j

## Reference Files
- **Functional requirements:** FUNCTIONAL.md
- **Architecture details:** ARCHITECTURE.md
- **Sample configuration:** config/schema_template.json