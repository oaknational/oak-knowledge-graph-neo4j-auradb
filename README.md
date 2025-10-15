# Oak Knowledge Graph Pipeline

A production-ready Python pipeline that extracts Oak National Academy curriculum data from Hasura materialized views and imports it into Neo4j AuraDB as a knowledge graph.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

This pipeline enables data engineers and curriculum teams to transform Oak's curriculum data into a queryable knowledge graph structure. The entire process is controlled through a single JSON configuration file, making it easy to customize schema mappings, data filters, and import behavior without code changes.

**Key Features:**
- **Multi-source extraction:** Query multiple Hasura materialized views with configurable joins (simple, composite keys)
- **Flexible data transformation:** JSON-based schema mapping with support for nested fields, synthetic values, and computed properties
- **Array expansion:** Optionally create separate nodes from array fields for granular relationship modeling
- **Native Neo4j types:** Automatic handling of lists, dates, and complex JSON objects
- **High-performance import:** Batch processing with automatic file splitting for large datasets (18,000+ records tested)
- **Data quality:** Unicode support, empty value filtering, and quote normalization
- **Selective execution:** Run extraction and import phases independently via configuration flags

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your Hasura and Neo4j credentials

# 3. Configure pipeline
# Edit config/oak_curriculum_schema_v0.1.0-alpha.json

# 4. Run pipeline
python main.py
```

## Documentation

- **[User Guide](USER_GUIDE.md)** - Complete configuration reference with examples
- **[Development History](HISTORY.md)** - Project evolution and technical decisions
- **[Architecture](ARCHITECTURE.md)** - System design and component responsibilities
- **[Functional Spec](FUNCTIONAL.md)** - Requirements and acceptance criteria
- **[Development Standards](CLAUDE.md)** - Code standards and quality gates

## Requirements

- **Python:** 3.10+ (required for Neo4j driver routing compatibility)
- **Hasura:** GraphQL endpoint with Oak authentication
- **Neo4j:** AuraDB instance or local Neo4j 5.0+

### Python Dependencies

```
pandas>=1.5.0           # Data transformation
requests>=2.28.0        # Hasura API client
neo4j>=5.0.0            # Database driver
python-dotenv>=1.0.0    # Environment management
black>=22.0.0           # Code formatting
flake8>=5.0.0           # Linting
pytest>=7.0.0           # Testing
```

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Configuration (JSON)                         │
│  • Materialized views    • Join strategy    • Schema mapping   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HASURA EXPORT PHASE                           │
│  (if export_from_hasura: true)                                  │
├─────────────────────────────────────────────────────────────────┤
│  1. HasuraExtractor  →  Query materialized views with joins     │
│  2. DataCleaner      →  Apply filters and preprocessing         │
│  3. Output           →  data/cleaned_mv_data.csv                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NEO4J IMPORT PHASE                           │
│  (if import_to_neo4j: true)                                     │
├─────────────────────────────────────────────────────────────────┤
│  4. SchemaMapper     →  Map CSV to Neo4j schema                 │
│  5. CSV Generation   →  Create node and relationship CSVs       │
│  6. AuraDBLoader     →  Batch import to Neo4j (UNWIND queries)  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── main.py                     # Pipeline entry point
├── config_manager.py           # Configuration loader
├── hasura_extractor.py         # Hasura GraphQL client
├── data_cleaner.py             # Data preprocessing
├── schema_mapper.py            # CSV to Neo4j mapping
├── auradb_loader.py            # Neo4j import executor
├── models/                     # Pydantic data models
├── utils/                      # Shared utilities
├── config/                     # JSON configuration files
│   └── oak_curriculum_schema_v0.1.0-alpha.json
├── tests/                      # Unit and integration tests
└── data/                       # Generated CSV files (gitignored)
```

## Configuration

The pipeline is controlled through a single JSON configuration file. Key sections:

### Control Flags
```json
{
  "export_from_hasura": true,      // Extract from Hasura
  "import_to_neo4j": true,         // Import to Neo4j
  "clear_database_before_import": true,
  "test_limit": null               // Limit records for testing
}
```

### Materialized Views
```json
{
  "materialized_views": {
    "published_mv_lessons": [
      "lesson_id",
      "lesson_slug",
      "lesson_title: lesson_data(path: \"title\")"
    ]
  }
}
```

### Join Strategy
```json
{
  "join_strategy": {
    "type": "multi_source_join",
    "primary_mv": "published_mv_lessons",
    "joins": [{
      "mv": "published_mv_units",
      "join_type": "left",
      "on": {
        "left_key": ["unit_slug", "programme_slug_by_year"],
        "right_key": ["unit_slug", "programme_slug_by_year"]
      }
    }]
  }
}
```

### Schema Mapping
```json
{
  "schema_mapping": {
    "nodes": {
      "Lesson": {
        "id_field": {
          "hasura_col": "lesson_slug",
          "type": "string",
          "property_name": "lessonSlug"
        },
        "properties": {
          "lessonTitle": {
            "hasura_col": "lesson_title",
            "type": "string"
          }
        }
      }
    },
    "relationships": {
      "unit_has_lesson": {
        "relationship_type": "HAS_LESSON",
        "start_node_type": "Unit",
        "start_csv_field": "unit_slug",
        "end_node_type": "Lesson",
        "end_csv_field": "lesson_slug"
      }
    }
  }
}
```

**See [USER_GUIDE.md](USER_GUIDE.md) for complete configuration reference.**

## Usage Examples

### Full Pipeline Execution
```bash
# Extract from Hasura and import to Neo4j
python main.py
```

### Extract Data Only
```json
// In config file:
{
  "export_from_hasura": true,
  "import_to_neo4j": false
}
```

### Import Previously Extracted Data
```json
// In config file:
{
  "export_from_hasura": false,
  "import_to_neo4j": true
}
```

### Test with Limited Data
```json
// In config file:
{
  "test_limit": 100,
  "filters": {
    "programme_keystage": "Key Stage 2"
  }
}
```

## Production Performance

Tested and validated with Oak production data:
- **Records processed:** 18,238+ curriculum records
- **Nodes created:** 16,526 across 13 node types
- **Relationships created:** 24,000+ across 14 relationship types
- **Batch size:** 1,000 records per UNWIND query
- **File handling:** Automatic splitting at 10,000 rows
- **Memory:** Optimized for large datasets with streaming processing

## Development

### Code Quality Standards

```bash
# Format code
black .

# Lint code
flake8

# Run tests
pytest tests/

# Run integration tests
./scripts/run_integration_tests.sh
```

All code must pass these quality gates before commit.

### Testing

```bash
# Unit tests only
pytest tests/test_*.py

# Integration tests (requires mock data)
pytest tests/test_integration.py

# Coverage report
pytest --cov=. tests/
```

## Environment Variables

Required variables in `.env` file:

```bash
# Hasura (Required for extraction)
HASURA_ENDPOINT=https://your-instance.hasura.app/v1/graphql
HASURA_API_KEY=your-128-character-oak-api-key
OAK_AUTH_TYPE=oak-admin

# Neo4j (Required for import)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Optional
LOG_LEVEL=INFO
LOG_FILE=pipeline.log
```

## Troubleshooting

### Common Issues

**Authentication failed:**
- Verify `HASURA_API_KEY` in `.env`
- Ensure `OAK_AUTH_TYPE=oak-admin` is set

**Join key mismatch:**
- Check that join keys exist in both materialized views
- Verify field names match exactly (case-sensitive)

**Type conversion errors:**
- Ensure schema mapping types match actual data types
- Check for null values in required fields

**Missing Neo4j properties:**
- Verify `hasura_col` names match CSV column names
- Use `snake_case` for CSV fields, `camelCase` for Neo4j properties

**See [USER_GUIDE.md](USER_GUIDE.md#troubleshooting) for complete troubleshooting guide.**

## Project Status

**Current Version:** v0.1.0-alpha
**Status:** Production-ready for Oak curriculum data

## License

Internal Oak National Academy project.

## Support

For questions or issues:
1. Review [USER_GUIDE.md](USER_GUIDE.md) for configuration help
2. Check [HISTORY.md](HISTORY.md) for recent changes and solutions
3. Consult [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

**Maintained by:** Oak National Academy - AI Enablement Squad
**Python Version:** 3.10+
**Last Updated:** October 2025
