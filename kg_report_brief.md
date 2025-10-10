# Brief: Generate Comprehensive Documentation for UK School Curriculum Neo4j Knowledge Graph

## Objective
Create comprehensive, professional documentation for a Neo4j knowledge graph representing the UK school curriculum structure. The documentation should serve both technical and non-technical audiences, making the graph accessible and demonstrating its practical value.

## Prerequisites
- You have access to the Neo4j database containing the UK curriculum graph
- First, run introspection queries to understand the complete schema

## Required Initial Analysis

Before writing documentation, execute these queries to understand the graph:

```cypher
// Get all node labels and counts
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`'+label+'`) RETURN count(n) as count', {})
YIELD value
RETURN label, value.count as count
ORDER BY label;

// Get all relationship types and counts
CALL db.relationshipTypes() YIELD relationshipType
CALL apoc.cypher.run('MATCH ()-[r:`'+relationshipType+'`]->() RETURN count(r) as count', {})
YIELD value
RETURN relationshipType, value.count as count
ORDER BY relationshipType;

// Sample properties for each node type
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`'+label+'`) RETURN n LIMIT 3', {})
YIELD value
RETURN label, value.n;

// Get relationship patterns
MATCH (a)-[r]->(b)
WITH labels(a)[0] as from, type(r) as rel, labels(b)[0] as to, count(*) as count
RETURN from, rel, to, count
ORDER BY count DESC;
```

## Documentation Structure

Create a comprehensive markdown document with the following sections:

### 1. Introduction
- **Title**: UK School Curriculum Knowledge Graph - Documentation & User Guide
- **Purpose**: Explain what the graph represents and key use cases
- **Benefits**: Why model curriculum as a graph? (relationships, traversal, flexibility)
- **Audience**: Who should use this (educators, curriculum planners, researchers, developers)

### 2. Executive Summary
- High-level overview of what's in the graph
- Key statistics (number of subjects, year groups, topics, etc.)
- Primary relationships modeled
- Quick example of a question the graph can answer

### 3. Graph Schema Documentation

#### 3.1 Visual Schema Diagram
- Create an ASCII art or description of the node types and their relationships
- Show the hierarchy and connections clearly

#### 3.2 Node Types
For EACH node label discovered, provide:
- **Label Name**
- **Description**: What this node represents
- **Properties**: List all properties with data types and example values
- **Cardinality**: Approximate count
- **Example instances**: 2-3 real examples from the graph

#### 3.3 Relationship Types
For EACH relationship type discovered, provide:
- **Relationship Type**
- **Description**: What this relationship means
- **Pattern**: `(SourceLabel)-[:RELATIONSHIP_TYPE]->(TargetLabel)`
- **Properties**: Any properties on the relationship
- **Cardinality**: Approximate count
- **Semantics**: Explain the meaning (e.g., "indicates that a Topic belongs to a Subject")

### 4. Data Model Deep Dive

Explain the curriculum structure:
- How are subjects organized?
- How are year groups/key stages represented?
- How are topics and learning objectives connected?
- Any hierarchical structures (parent-child relationships)
- Cross-cutting relationships (prerequisites, related topics, etc.)

### 5. Getting Started

#### 5.1 Connection Information
```
Neo4j Browser URL: bolt://localhost:7687
Username: [if applicable]
Note: [any connection details]
```

#### 5.2 Basic Query Examples
Provide 5-7 simple queries for newcomers:
- Count all nodes of each type
- Find all subjects
- Find topics for a specific year group
- Find learning objectives for a subject
- Show the structure for a single subject

### 6. Common Query Patterns

#### 6.1 Curriculum Navigation
- Finding all content for a year group
- Listing topics within a subject
- Exploring learning progressions

#### 6.2 Relationship Traversal
- Finding prerequisites for a topic
- Discovering related topics across subjects
- Mapping curriculum paths

#### 6.3 Analysis Queries
- Subject complexity analysis
- Coverage analysis by year group
- Cross-curricular connections

For EACH pattern, provide:
- Use case description
- Cypher query with comments
- Sample results (formatted as a table or list)
- Explanation of what the query does

### 7. Practical Use Cases

Develop 8-12 real-world scenarios with complete examples:

#### Example Use Cases:
- "Find all topics a Year 7 student studies in Mathematics"
- "Show the learning progression for [specific topic] across year groups"
- "Find topics that connect Mathematics and Science"
- "List all prerequisites for studying [advanced topic]"
- "Generate a term plan for [subject] in [year group]"
- "Identify gaps in curriculum coverage"
- "Find topics suitable for cross-curricular projects"
- "Map dependencies between topics to create a learning pathway"

For each use case:
1. **Scenario**: Describe the real-world need
2. **Query**: Provide the Cypher query with inline comments
3. **Results**: Show actual results from the graph (formatted clearly)
4. **Interpretation**: Explain what the results mean
5. **Variations**: Suggest how to modify the query for related needs

### 8. Advanced Queries

#### 8.1 Multi-hop Traversals
- Finding indirect relationships (e.g., topics connected through multiple paths)
- Curriculum dependency chains

#### 8.2 Pattern Matching
- Complex patterns (e.g., topics that appear in multiple subjects)
- Optional patterns for flexible queries

#### 8.3 Aggregations and Analytics
- Statistics about the curriculum structure
- Coverage metrics
- Complexity analysis

#### 8.4 Graph Algorithms (if applicable)
- Shortest path between topics
- Centrality measures (which topics are most connected)
- Community detection (natural groupings)

### 9. Query Optimization Tips
- Indexing recommendations
- Query performance best practices
- Common pitfalls to avoid

### 10. Data Quality Notes
- Known limitations or gaps
- Update frequency
- Data sources and methodology
- Version information

### 11. Appendices

#### Appendix A: Complete Cypher Reference
Quick reference of all queries in the document

#### Appendix B: Property Reference
Complete list of all properties across all node types

#### Appendix C: Glossary
Definitions of UK curriculum terms and concepts

## Formatting Requirements

- Use clear markdown headers (##, ###, ####)
- Include code blocks with ```cypher syntax highlighting
- Format results as tables where appropriate
- Use **bold** for emphasis on key terms
- Include horizontal rules (---) to separate major sections
- Add a table of contents at the beginning
- Include "💡 Tip" or "⚠️ Note" callouts for important information

## Quality Standards

- All queries must be tested against the actual database
- Results must be real data from the graph, not placeholder examples
- Explanations should be clear for non-technical curriculum specialists
- Technical accuracy for developers using the graph
- Include at least 20 different practical query examples
- Ensure queries cover all major node types and relationships

## Deliverable

A single comprehensive markdown file named `UK_CURRICULUM_GRAPH_DOCUMENTATION.md` that:
- Is 3000-5000 lines long
- Serves as both a user guide and technical reference
- Includes real examples from the actual graph
- Can be easily converted to PDF or HTML if needed
- Is immediately useful for someone new to the graph

## Success Criteria

The documentation should enable a user to:
1. Understand the structure and purpose of the graph within 5 minutes
2. Run their first successful query within 10 minutes
3. Build custom queries for their needs within 30 minutes
4. Appreciate the power of the graph model for curriculum analysis

---

**Start by running the introspection queries to understand the schema, then build the documentation systematically, section by section. Make it comprehensive, practical, and exemplary.**