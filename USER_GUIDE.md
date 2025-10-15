# Oak Knowledge Graph Pipeline - User Guide

## Overview

This pipeline extracts Oak curriculum data from Hasura materialized views, transforms it, and imports it into a Neo4j knowledge graph. The entire process is controlled through a single JSON configuration file.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 3. Edit configuration file
# Edit config/oak_curriculum_schema_v0.1.0-alpha.json

# 4. Run the pipeline
python main.py
```

## Environment Setup

Create a `.env` file in the project root with the following variables:

```bash
# Required: Hasura connection
HASURA_ENDPOINT=https://your-hasura-instance.hasura.app/v1/graphql
HASURA_API_KEY=your-128-character-oak-api-key
OAK_AUTH_TYPE=oak-admin

# Required for Neo4j import: Database connection
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-secure-password

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=pipeline.log
```

---

## Configuration File Structure

The pipeline uses a JSON configuration file that controls all aspects of data extraction, transformation, and import. The active configuration is:

```
config/oak_curriculum_schema_v0.1.0-alpha.json
```

### Top-Level Settings

```json
{
  "hasura_endpoint": "${HASURA_ENDPOINT}",
  "export_from_hasura": true,
  "import_to_neo4j": true,
  "test_limit": null,
  "clear_database_before_import": true,
  "materialized_views": { ... },
  "join_strategy": { ... },
  "filters": { ... },
  "schema_mapping": { ... }
}
```

#### Control Flags

| Setting | Type | Description |
|---------|------|-------------|
| `export_from_hasura` | boolean | Set to `true` to extract data from Hasura, `false` to skip |
| `import_to_neo4j` | boolean | Set to `true` to import to Neo4j, `false` to skip |
| `clear_database_before_import` | boolean | Set to `true` to clear existing Neo4j data before import |
| `test_limit` | number/null | Limit number of records for testing (e.g., `100`), or `null` for all records |

**Example: Extract Only**
```json
{
  "export_from_hasura": true,
  "import_to_neo4j": false
}
```

**Example: Import Only (Using Previously Exported Data)**
```json
{
  "export_from_hasura": false,
  "import_to_neo4j": true
}
```

---

## Materialized Views Configuration

The `materialized_views` section specifies which Hasura materialized views to query and which fields to extract.

### Structure

```json
"materialized_views": {
  "view_name": [
    "field1",
    "field2: nested_field(path: \"json.path\")",
    "field3"
  ]
}
```

### Field Extraction Syntax

**Simple Fields:**
```json
"unitvariant_id"
```

**JSON Path Extraction:**
```json
"lesson_title: lesson_data(path: \"title\")"
```
This extracts the `title` field from the `lesson_data` JSON column and names it `lesson_title`.

**Nested JSON Paths:**
```json
"unit_order: supplementary_data(path: \"unit_order\")"
```

### Example: Single View

```json
"materialized_views": {
  "published_mv_curriculum_units": [
    "unit_id",
    "unit_slug",
    "unit_title: unit_data(path: \"title\")",
    "unit_description: unit_data(path: \"description\")"
  ]
}
```

### Example: Multiple Views

```json
"materialized_views": {
  "published_mv_lessons": [
    "lesson_id",
    "lesson_slug",
    "lesson_title"
  ],
  "published_mv_units": [
    "unit_id",
    "unit_slug",
    "unit_title"
  ]
}
```

---

## Join Strategy Configuration

When extracting from multiple materialized views, define how to join them.

### Single Source (No Joins)

```json
"join_strategy": {
  "type": "single_source"
}
```

### Multi-Source Join

```json
"join_strategy": {
  "type": "multi_source_join",
  "primary_mv": "published_mv_primary",
  "joins": [
    {
      "mv": "published_mv_secondary",
      "join_type": "left",
      "on": {
        "left_key": "unit_slug",
        "right_key": "unit_slug"
      }
    }
  ]
}
```

#### Join Types

- `left`: Keep all records from primary view
- `inner`: Keep only matching records
- `right`: Keep all records from secondary view
- `outer`: Keep all records from both views

### Composite Key Joins

For more precise matching across multiple fields:

```json
"join_strategy": {
  "type": "multi_source_join",
  "primary_mv": "published_mv_lessons",
  "joins": [
    {
      "mv": "published_mv_units",
      "join_type": "left",
      "on": {
        "left_key": ["unit_slug", "programme_slug_by_year"],
        "right_key": ["unit_slug", "programme_slug_by_year"]
      }
    }
  ]
}
```

**Note:** The pipeline automatically handles array-type fields in join keys by exploding them before joining.

---

## Data Filters

Apply filters during data cleaning to include only specific records.

### Structure

```json
"filters": {
  "field_name": value
}
```

### Examples

**Boolean Filter:**
```json
"filters": {
  "is_legacy": false
}
```

**Array Filter (Match Any):**
```json
"filters": {
  "programme_subject": ["History", "Maths", "English"]
}
```

**String Filter:**
```json
"filters": {
  "programme_keystage": "Key Stage 2"
}
```

**Multiple Filters (All Must Match):**
```json
"filters": {
  "is_legacy": false,
  "programme_keystage": "Key Stage 2",
  "programme_subject": ["History", "Geography"]
}
```

**No Filters:**
```json
"filters": {}
```

---

## Schema Mapping: Nodes

The `schema_mapping.nodes` section defines how CSV data maps to Neo4j nodes.

### Node Structure

```json
"NodeType": {
  "id_field": {
    "hasura_col": "csv_column_name",
    "type": "string|int|float|boolean",
    "property_name": "neoPropertyName",
    "synthetic_value": ""
  },
  "properties": {
    "neoPropertyName": {
      "hasura_col": "csv_column_name",
      "type": "string|int|float|boolean|list",
      "synthetic_value": ""
    }
  }
}
```

### Field Types

| Type | Description | Example Value |
|------|-------------|---------------|
| `string` | Text value | `"History"` |
| `int` | Integer number | `42` |
| `float` | Decimal number | `3.14` |
| `boolean` | True/false | `true` |
| `list` | Array of values | `["item1", "item2"]` |
| `datetime` | Timestamp | `"2025-01-15T10:30:00Z"` |

### Example: Basic Node

```json
"Subject": {
  "id_field": {
    "hasura_col": "programme_subject_slug",
    "type": "string",
    "property_name": "subjectSlug"
  },
  "properties": {
    "subjectTitle": {
      "hasura_col": "programme_subject",
      "type": "string"
    },
    "subjectId": {
      "hasura_col": "programme_subject_id",
      "type": "int"
    }
  }
}
```

This creates nodes like:
```cypher
(:Subject {subjectSlug: "history", subjectTitle: "History", subjectId: 123})
```

### Example: Node with List Properties

```json
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
    },
    "keyLearningPoints": {
      "hasura_col": "lesson_key_learning_points",
      "type": "list"
    }
  }
}
```

List properties are stored as native Neo4j arrays. Complex objects within arrays are stored as JSON strings.

### Synthetic Values

Create fields with computed or constant values:

```json
"Schemaversion": {
  "id_field": {
    "hasura_col": "",
    "type": "string",
    "property_name": "schemaVersion",
    "synthetic_value": "v0.1.0-alpha"
  },
  "properties": {
    "isActive": {
      "hasura_col": "",
      "type": "boolean",
      "synthetic_value": true
    }
  }
}
```

### Composite Synthetic Values

Combine multiple fields:

```json
"Unitoffering": {
  "id_field": {
    "hasura_col": "",
    "type": "string",
    "property_name": "unitOfferingSlug",
    "synthetic_value": "{programme_year_slug}-{programme_subject_slug}"
  }
}
```

This creates IDs like `"year-5-history"` by combining field values.

### Array Expansion

Create separate nodes from array fields:

```json
"Thread": {
  "id_field": {
    "hasura_col": "threads",
    "type": "string",
    "expand_list": true,
    "property_name": "thread_slug"
  },
  "properties": {
    "threadId": {
      "hasura_col": "thread_id",
      "type": "int"
    },
    "threadTitle": {
      "hasura_col": "thread_title",
      "type": "string"
    }
  }
}
```

**Without `expand_list`:** One node with `threads` as a list property
**With `expand_list: true`:** Separate Thread node for each item in the threads array

---

## Schema Mapping: Relationships

The `schema_mapping.relationships` section defines connections between nodes.

### Relationship Structure

```json
"config_key": {
  "relationship_type": "NEO4J_TYPE",
  "start_node_type": "NodeType",
  "start_csv_field": "csv_column_name",
  "end_node_type": "NodeType",
  "end_csv_field": "csv_column_name",
  "properties": {
    "propertyName": {
      "hasura_col": "csv_column_name",
      "type": "string|int|float|boolean"
    }
  }
}
```

### Example: Basic Relationship

```json
"subject_has_unit": {
  "relationship_type": "HAS_UNIT",
  "start_node_type": "Subject",
  "start_csv_field": "programme_subject_slug",
  "end_node_type": "Unit",
  "end_csv_field": "unit_slug",
  "properties": {}
}
```

Creates:
```cypher
(:Subject {subjectSlug: "history"})-[:HAS_UNIT]->(:Unit {unitSlug: "vikings"})
```

### Example: Relationship with Properties

```json
"unitvariant_has_lesson": {
  "relationship_type": "HAS_LESSON",
  "start_node_type": "Unitvariant",
  "start_csv_field": "unitvariant_id",
  "end_node_type": "Lesson",
  "end_csv_field": "lesson_slug",
  "properties": {
    "lessonOrder": {
      "hasura_col": "order_in_unit",
      "type": "int"
    }
  }
}
```

Creates:
```cypher
(:Unitvariant)-[:HAS_LESSON {lessonOrder: 1}]->(:Lesson)
```

### Computed Relationship Properties

Derive boolean values from field presence:

```json
"programme_has_unitvariant": {
  "relationship_type": "HAS_UNITVARIANT",
  "start_node_type": "Programme",
  "start_csv_field": "programme_slug_by_year",
  "end_node_type": "Unitvariant",
  "end_csv_field": "unitvariant_id",
  "properties": {
    "isOptional": {
      "hasura_col": "programme_optionality",
      "type": "boolean",
      "computed": "is_not_null"
    }
  }
}
```

**Computed Options:**
- `is_null`: Returns `true` if field is null/empty, `false` otherwise
- `is_not_null`: Returns `true` if field has a value, `false` if null/empty

### Relationships with Array Expansion

When the end node uses array expansion, the relationship automatically expands:

```json
"unit_has_thread": {
  "relationship_type": "HAS_THREAD",
  "start_node_type": "Unit",
  "start_csv_field": "unit_slug",
  "end_node_type": "Thread",
  "end_csv_field": "threads",
  "properties": {}
}
```

If `threads` is `[{thread_slug: "t1"}, {thread_slug: "t2"}]`, this creates:
```cypher
(:Unit)-[:HAS_THREAD]->(:Thread {threadSlug: "t1"})
(:Unit)-[:HAS_THREAD]->(:Thread {threadSlug: "t2"})
```

---

## Common Configuration Patterns

### Pattern 1: Extract All Data, Full Import

```json
{
  "export_from_hasura": true,
  "import_to_neo4j": true,
  "clear_database_before_import": true,
  "test_limit": null,
  "filters": {}
}
```

**Use Case:** Initial setup or complete refresh

### Pattern 2: Test with Subset

```json
{
  "export_from_hasura": true,
  "import_to_neo4j": true,
  "clear_database_before_import": true,
  "test_limit": 100,
  "filters": {
    "programme_keystage": "Key Stage 2"
  }
}
```

**Use Case:** Testing configuration changes with limited data

### Pattern 3: Re-import Existing Data

```json
{
  "export_from_hasura": false,
  "import_to_neo4j": true,
  "clear_database_before_import": true
}
```

**Use Case:** Schema changes without re-extracting from Hasura

### Pattern 4: Extract Only

```json
{
  "export_from_hasura": true,
  "import_to_neo4j": false
}
```

**Use Case:** Data inspection, CSV generation for external tools

### Pattern 5: Incremental Update

```json
{
  "export_from_hasura": true,
  "import_to_neo4j": true,
  "clear_database_before_import": false,
  "filters": {
    "lesson_created_at": "2025-01-01"
  }
}
```

**Use Case:** Adding new records without clearing existing data

---

## Running the Pipeline

### Basic Execution

```bash
python main.py
```

The pipeline runs phases based on configuration flags:
- **Hasura Export Phase** (if `export_from_hasura: true`)
  1. Clear output files
  2. Extract data from materialized views
  3. Join views (if multi-source)
  4. Clean and filter data
  5. Save to `data/cleaned_mv_data.csv`

- **Neo4j Import Phase** (if `import_to_neo4j: true`)
  6. Map data to schema
  7. Generate node and relationship CSVs
  8. Import to Neo4j via batch queries

### Output Files

All generated files are in the `data/` directory:

**Export Phase:**
```
data/
├── hasura_export_raw.csv           # Raw Hasura data
└── cleaned_mv_data.csv             # Cleaned and filtered
```

**Import Phase:**
```
data/
├── Subject_nodes.csv               # Node CSVs
├── Unit_nodes.csv
├── Lesson_nodes.csv
├── subject_has_unit_rels.csv       # Relationship CSVs
└── unit_has_lesson_rels.csv
```

**Note:** Large files (>10,000 rows) are automatically split:
```
Lesson_nodes_part1.csv
Lesson_nodes_part2.csv
```

### Monitoring Progress

The pipeline outputs detailed progress information:

```
[INFO] Starting Hasura Export Phase
[INFO] Extracting from published_mv_lessons...
[INFO] Extracted 18,238 records
[INFO] Applying filters...
[INFO] Cleaning data...
[INFO] Saved to data/cleaned_mv_data.csv

[INFO] Starting Neo4j Import Phase
[INFO] Mapping schema...
[INFO] Generated 2,053 Subject nodes
[INFO] Generated 12,473 Lesson nodes
[INFO] Created 15,218 relationships
[INFO] Pipeline completed successfully
```

---

## Troubleshooting

### Common Issues

**1. Authentication Error**
```
Error: Hasura authentication failed
```
**Solution:** Check `HASURA_API_KEY` in `.env` file

**2. Join Key Mismatch**
```
Error: No matching records in join
```
**Solution:** Verify join key fields exist in both views

**3. Type Conversion Error**
```
Error: Cannot convert 'abc' to int
```
**Solution:** Check field types in schema mapping match actual data

**4. Missing Properties in Neo4j**
```
Warning: Property 'unitOrder' not found on relationships
```
**Solution:** Verify `hasura_col` in relationship properties matches CSV column name

**5. Empty Node Sets**
```
Warning: Generated 0 nodes for type 'Thread'
```
**Solution:** Check if source field contains data, verify filters aren't too restrictive

### Validation Checklist

Before running:
- [ ] `.env` file configured with valid credentials
- [ ] `export_from_hasura` and `import_to_neo4j` flags set correctly
- [ ] Materialized view names match Hasura schema
- [ ] Field names in `hasura_col` match CSV columns (use snake_case)
- [ ] Property names in `property_name` use Neo4j conventions (camelCase)
- [ ] Node types and relationship types use proper capitalization
- [ ] All join key fields exist in both views
- [ ] Filters use valid field names from extracted data

---

## Performance Optimization

### Large Datasets

For datasets over 50,000 records:

1. **Use filters** to process subsets:
```json
"filters": {
  "programme_keystage": "Key Stage 2"
}
```

2. **Test with limits** first:
```json
"test_limit": 1000
```

3. **Process in batches** by key stage or subject

### Memory Management

The pipeline automatically:
- Processes CSV files in chunks
- Splits large files (10,000+ rows)
- Uses batch queries (1,000 records per batch)
- Cleans up intermediate data

### Database Performance

To preserve existing data during development:
```json
"clear_database_before_import": false
```

To start fresh:
```json
"clear_database_before_import": true
```

---

## Best Practices

### Configuration Management

1. **Version control:** Keep configuration files in git
2. **Use descriptive names:** Name config files clearly (e.g., `ks2_history_only.json`)
3. **Document changes:** Add comments to `_comments` section
4. **Test incrementally:** Use `test_limit` when testing schema changes
5. **Keep backups:** Save working configurations before major changes

### Schema Design

1. **Use semantic naming:** Choose clear, descriptive property names
2. **Follow Neo4j conventions:** PascalCase for node types, UPPER_SNAKE for relationships
3. **Minimize array expansion:** Only expand arrays when separate nodes are truly needed
4. **Add timestamps:** Include `lastUpdated` properties for tracking
5. **Use computed properties:** Derive booleans from field presence when appropriate

### Data Quality

1. **Apply filters early:** Filter in extraction phase, not just in Neo4j queries
2. **Validate joins:** Check row counts before and after joins
3. **Inspect CSVs:** Review generated CSV files before importing
4. **Use test limits:** Validate with small datasets first
5. **Monitor logs:** Check for warnings about missing data or type mismatches

---

## Configuration Reference Summary

### Minimum Required Configuration

```json
{
  "hasura_endpoint": "${HASURA_ENDPOINT}",
  "export_from_hasura": true,
  "import_to_neo4j": true,
  "materialized_views": {
    "view_name": ["field1", "field2"]
  },
  "join_strategy": {
    "type": "single_source"
  },
  "schema_mapping": {
    "nodes": {
      "NodeType": {
        "id_field": {
          "hasura_col": "id_field",
          "type": "string",
          "property_name": "id"
        },
        "properties": {}
      }
    },
    "relationships": {}
  }
}
```

### Full Configuration Template

See `config/oak_curriculum_schema_v0.1.0-alpha.json` for a complete working example with:
- 2 materialized views with composite key joins
- 13 node types including array expansion
- 14 relationship types with properties
- Filters, synthetic values, and computed properties

---

## Support

For issues or questions:
1. Check `HISTORY.md` for recent changes and solutions
2. Review `ARCHITECTURE.md` for technical details
3. Consult `CLAUDE.md` for development standards
4. Examine `FUNCTIONAL.md` for requirements

**Configuration Questions:**
- Verify field names match Hasura schema
- Check data types match actual data
- Ensure join keys exist in both views
- Validate Neo4j naming conventions

**Pipeline Errors:**
- Review log output for specific error messages
- Check `.env` file for credential issues
- Verify Hasura and Neo4j connectivity
- Inspect generated CSV files for data issues
