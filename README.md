# oak-knowledge-graph-neo4j-auradb
Simple batch job to extract Oak Curriculum data from Hasura materialized views, optionally clean the data, and import into a Neo4j knowledge graph. This is currently an MVP being led by the AI Enablement squad.

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## Architecture
1. Extract data from specified Hasura materialized views
2. Join all MV data into single consolidated CSV
3. Optional data cleaning/preprocessing area
4. Map CSV fields to knowledge graph schema via JSON configuration
5. Import directly into Neo4j knowledge graph
