# Simplified Batch Job Implementation TO-DO

## Phase 1: Foundation Setup

### ✅ Task 1: Environment Setup
**Description:** Set up basic project structure and dependencies
**Deliverables:**
- ✅ Updated `requirements.txt` with core dependencies (no Streamlit needed)
- ✅ Created directory structure (simplified flat structure)
- ✅ Basic `.gitignore` for Python projects
- ✅ Environment variables configuration

**Dependencies:** None
**Status:** COMPLETED

---

### ❌ Task 2: Data Models (REMOVED)
**Description:** ~~Create core data validation models~~ - REMOVED FOR SIMPLICITY
**Deliverables:**
- ❌ ~~Pydantic models~~ - Using plain Python dictionaries instead
- ✅ Simple JSON configuration loading
- ✅ Basic dictionary validation

**Dependencies:** Task 1
**Status:** SIMPLIFIED - No longer using complex data models

---

### ✅ Task 3: Configuration Management (SIMPLIFIED)
**Description:** Simple JSON configuration loading
**Deliverables:**
- ✅ `config_manager.py` - Simple JSON loading and basic validation
- ✅ JSON configuration files in `/config` directory
- ✅ Environment variable handling for credentials
- ❌ ~~Pydantic validation~~ - Removed for simplicity

**Dependencies:** Task 1
**Status:** COMPLETED - Simplified to plain dictionaries

---

### ✅ Task 4: Logging and Utilities
**Description:** Implement logging and shared utilities
**Deliverables:**
- ✅ `utils/logging.py` - Logging configuration
- ✅ `utils/helpers.py` - Shared utility functions
- ✅ Console logging setup

**Dependencies:** Task 1
**Status:** COMPLETED

---

## Phase 2: Core Batch Components

### ✅ Task 5: Hasura Extractor
**Description:** Extract and join data from specified Hasura materialized views
**Deliverables:**
- ✅ `hasura_extractor.py` - HasuraExtractor class
- ✅ GraphQL query generation and execution
- ✅ Data joining into single consolidated CSV
- ✅ Authentication and error handling

**Dependencies:** Task 3
**Status:** COMPLETED

---

### 🔄 Task 6: Data Cleaner (NEW)
**Description:** Optional data preprocessing area
**Deliverables:**
- ⚠️ `data_cleaner.py` - DataCleaner class with extensible cleaning methods
- ⚠️ Load consolidated CSV, apply cleaning transformations
- ⚠️ Save cleaned CSV for inspection/debugging
- ⚠️ Clear area for user to add custom cleaning logic

**Dependencies:** Task 5
**Status:** NEEDS IMPLEMENTATION

---

### ✅ Task 7: Schema Mapper
**Description:** Map CSV fields to knowledge graph schema
**Deliverables:**
- ✅ `schema_mapper.py` - SchemaMapper class
- ✅ CSV field to graph property mapping
- ✅ Node and relationship mapping logic
- ✅ Field transformation rules

**Dependencies:** Task 3, Task 6
**Status:** COMPLETED

---

### ✅ Task 8: Neo4j Loader
**Description:** Direct import into Neo4j knowledge graph
**Deliverables:**
- ✅ `neo4j_loader.py` - Neo4jLoader class
- ✅ Direct database import (no CSV generation needed)
- ✅ Node and relationship creation
- ✅ Import statistics and validation

**Dependencies:** Task 7
**Status:** COMPLETED

---

## Phase 3: Batch Orchestration

### 🔄 Task 9: Batch Processor (REVISED)
**Description:** Simple linear batch job orchestration
**Deliverables:**
- ⚠️ `batch_processor.py` - Main BatchProcessor class
- ⚠️ Linear execution flow: Extract → Join → Clean → Map → Import
- ⚠️ Progress reporting to console
- ⚠️ Error handling and graceful exit

**Dependencies:** Task 5, Task 6, Task 7, Task 8
**Status:** NEEDS SIMPLIFICATION (Pipeline exists but needs to be simplified)

---

### 🔄 Task 10: Main Entry Point (REVISED)
**Description:** Simple batch job entry point
**Deliverables:**
- ⚠️ `main.py` - Single command execution (remove CLI complexity)
- ⚠️ Load configuration from JSON file
- ⚠️ Execute BatchProcessor
- ⚠️ Console progress and error reporting

**Dependencies:** Task 9
**Status:** NEEDS SIMPLIFICATION (CLI exists but needs to be simplified to batch job)

---

## Phase 4: Testing and Validation

### ✅ Task 11: Unit Tests
**Description:** Basic unit tests for core components
**Deliverables:**
- ✅ `tests/test_config_manager.py` - Configuration tests
- ✅ `tests/test_extractors.py` - Extraction logic tests
- ✅ `tests/test_mappers.py` - Schema mapping tests
- ✅ `tests/test_pipeline.py` - Pipeline orchestration tests
- ✅ Test fixtures for mocking API responses

**Dependencies:** Task 9
**Status:** COMPLETED

---

### ✅ Task 12: Integration Testing
**Description:** End-to-end testing with sample data
**Deliverables:**
- ✅ `tests/test_integration.py` - Integration tests
- ✅ Sample configuration files
- ✅ Mock data validation

**Dependencies:** Task 11
**Status:** COMPLETED

---

## Phase 5: Cleanup and Simplification

### ❌ Task 13: Remove Unnecessary Components (EXPANDED)
**Description:** Remove components not needed for simple batch job
**Deliverables:**
- ❌ Remove `streamlit_app.py` (no UI needed)
- ❌ Remove complex CLI arguments from `main.py`
- ❌ Remove Strategy pattern complexity if not needed
- ❌ Simplify Pipeline to BatchProcessor
- ❌ Remove `models/` directory and pydantic models
- ❌ Update requirements.txt to remove Streamlit and pydantic

**Dependencies:** Task 10
**Status:** PENDING

---

### ✅ Task 14: Code Quality Validation
**Description:** Ensure code meets quality standards
**Deliverables:**
- ✅ Code passes `black --check .`
- ✅ Code passes `flake8`
- ✅ Unit tests pass

**Dependencies:** Task 13
**Status:** COMPLETED

---

### ✅ Task 15: Documentation Update
**Description:** Updated documentation for simplified architecture
**Deliverables:**
- ✅ Updated CLAUDE.md, FUNCTIONAL.md, ARCHITECTURE.md
- ✅ Updated README.md for simple batch execution
- ✅ Updated BRIEF.md for simplified flow

**Dependencies:** Task 14
**Status:** COMPLETED

---

## Current Implementation Status

### ✅ COMPLETED (Already Implemented)
- Foundation setup and project structure
- Simple JSON configuration loading and basic validation
- Configuration management with JSON files
- Hasura data extraction with authentication
- Schema mapping from CSV to knowledge graph
- Neo4j loader for direct database import
- Comprehensive unit and integration tests
- Logging and utilities
- Updated documentation

### 🔄 NEEDS WORK (Partially Complete)
- Data cleaning component (needs implementation)
- Batch processor simplification (Pipeline exists but too complex)
- Main entry point simplification (CLI exists but needs to be batch job)

### ❌ TO BE REMOVED
- Streamlit web interface
- Complex CLI argument parsing
- Strategy pattern complexity (if not needed)
- Streamlit dependency
- Pydantic models and dependency
- Models directory with complex validation

## Simplified Dependency Chain

```
✅ Environment & Models → ✅ Config Management → ✅ Hasura Extractor
                                                        ↓
⚠️ Data Cleaner → ✅ Schema Mapper → ✅ Neo4j Loader
                                            ↓
                              ⚠️ Batch Processor → ⚠️ Simple main.py
                                            ↓
                                    ❌ Remove Unnecessary → ✅ Final Validation
```

## Critical Path for Completion
1. **Implement Data Cleaner** - Create optional preprocessing area
2. **Simplify Batch Processor** - Remove Pipeline complexity, create linear BatchProcessor
3. **Simplify main.py** - Remove CLI complexity, make simple batch execution
4. **Remove Unnecessary Components** - Clean up Streamlit, pydantic models, and complex features
5. **Final Testing** - Ensure simplified batch job works end-to-end

## Estimated Effort Remaining
- **High Priority:** Tasks 6, 9, 10 (core functionality)
- **Medium Priority:** Task 13 (cleanup)
- **Total:** ~4-6 hours of development work