# Oak Curriculum Migration Package

Python-based migration tools for Oak curriculum data extraction and Neo4j migration.

## Overview

This package provides complete migration pipeline utilities to:

1. **Analyze** the curriculum data structure via Hasura's GraphQL API (Task 29)
2. **Map** core curriculum tables to Neo4j graph schema (Task 30)  
3. **Extract** curriculum data from PostgreSQL to CSV format (Task 31)
4. **Transform** relational CSV data to graph-optimized format (Task 32)
5. **Load** data into Neo4j AuraDB (Task 33)
6. **Validate** migration success with comprehensive checks (Task 34)

## Quick Start

### 1. Install Dependencies

```bash
cd packages/migration
pip3 install -r python/requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Hasura and Neo4j credentials
```

### 3. Run Migration Pipeline

**Task 29 - Analyze PostgreSQL Schema:**
```bash
python3 python/discover_base_schema.py
```

**Task 31 - Extract Curriculum Data:**
```bash
# Extract specific table with sample
python3 python/migration/extract_curriculum_data.py --table=pf_subjects --sample-size=10

# Extract all core tables
python3 python/migration/extract_curriculum_data.py

# Custom configuration
python3 python/migration/extract_curriculum_data.py --output-dir=./custom --batch-size=500 --no-validation
```

## Data Extraction (Task 31)

### Features
- **Batch Processing**: Configurable batch sizes with progress tracking
- **Data Validation**: Validates empty rows, null percentages, duplicate IDs  
- **CSV Export**: Organized output (`raw_data/`, `samples/`, `logs/`)
- **Error Handling**: Comprehensive logging and graceful error recovery
- **SSL Support**: Development-friendly configuration for Hasura Cloud

### Output Structure
```
python/output/
├── raw_data/           # Full dataset exports
├── samples/            # Sample datasets for development
├── logs/              # Extraction logs with timestamps
└── extraction_report_YYYYMMDD_HHMMSS.json
```

## Environment Variables

### Required

```bash
# Hasura GraphQL API (for schema analysis)
HASURA_ENDPOINT=https://your-endpoint.hasura.app/v1/graphql
HASURA_ADMIN_SECRET=your-admin-secret
```

## Files Recovered

- `python/discover_base_schema.py` - PostgreSQL schema discovery
- `python/migration/extract_curriculum_data.py` - Data extraction module
- `python/migration/__init__.py` - Migration package initialization
- `python/requirements.txt` - Python dependencies
- `python/base-schema-analysis.json` - Sample schema analysis results