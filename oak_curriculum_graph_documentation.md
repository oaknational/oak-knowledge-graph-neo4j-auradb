# Oak Curriculum Knowledge Graph
## Documentation & User Guide

**Schema Version:** v0.1.0-alpha 
**Last Updated:** October 2025 
**Schema:** Oak National Academy Curriculum Graph 

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [Purpose](#purpose)
   - [Benefits of Graph Modeling](#benefits-of-graph-modeling)
   - [Target Audience](#target-audience)

2. [Executive Summary](#2-executive-summary)
   - [Graph Overview](#graph-overview)
   - [Key Statistics](#key-statistics)
   - [Primary Relationships](#primary-relationships)
   - [Quick Example](#quick-example)

3. [Graph Schema Documentation](#3-graph-schema-documentation)
   - [Visual Schema Diagram](#31-visual-schema-diagram)
   - [Node Types](#32-node-types)
   - [Relationship Types](#33-relationship-types)

4. [Data Model Deep Dive](#4-data-model-deep-dive)
   - [Curriculum Structure](#curriculum-structure)
   - [Hierarchical Relationships](#hierarchical-relationships)
   - [Cross-Cutting Relationships](#cross-cutting-relationships)

5. [Getting Started](#5-getting-started)
   - [Connection Information](#51-connection-information)
   - [Basic Query Examples](#52-basic-query-examples)

6. [Common Query Patterns](#6-common-query-patterns)
   - [Curriculum Navigation](#61-curriculum-navigation)
   - [Relationship Traversal](#62-relationship-traversal)
   - [Analysis Queries](#63-analysis-queries)

7. [Practical Use Cases](#7-practical-use-cases)

8. [Advanced Queries](#8-advanced-queries)
   - [Multi-hop Traversals](#81-multi-hop-traversals)
   - [Pattern Matching](#82-pattern-matching)
   - [Aggregations and Analytics](#83-aggregations-and-analytics)
   - [Graph Algorithms](#84-graph-algorithms)

9. [Query Optimization Tips](#9-query-optimization-tips)

10. [Data Quality Notes](#10-data-quality-notes)

11. [Appendices](#11-appendices)
    - [Appendix A: Complete Cypher Reference](#appendix-a-complete-cypher-reference)
    - [Appendix B: Property Reference](#appendix-b-property-reference)
    - [Appendix C: Glossary](#appendix-c-glossary)

---

## 1. Introduction

### Purpose

The UK School Curriculum Knowledge Graph is a comprehensive Neo4j database that models the entire structure of the UK school curriculum from the Oak National Academy. This graph database captures the relationships between educational levels (phases, key stages, years), subjects, curriculum units, and individual lessons, along with rich metadata including learning objectives, keywords, teaching resources, and assessment information.

**What this graph represents:**
- Complete UK curriculum structure from primary through secondary education
- 12,631 individual lessons with detailed pedagogical content
- Curriculum organization across 22 subjects and 1,564 units
- Exam board specifications and tiered qualifications
- Thematic learning threads that span across units

**Key use cases:**
- **Curriculum Planning:** Discover and sequence learning content for term and year plans
- **Pedagogical Analysis:** Explore learning progressions and prerequisite knowledge
- **Cross-Curricular Connections:** Identify topics that link multiple subjects
- **Assessment Preparation:** Navigate exam board-specific content and tiered qualifications
- **Resource Discovery:** Find lessons by keyword, learning objective, or educational level
- **Data-Driven Insights:** Analyze curriculum coverage, complexity, and relationships

### Benefits of Graph Modeling

Traditional relational databases struggle to represent the complex, interconnected nature of curriculum data. Graph databases excel at this challenge:

**🔗 Natural Relationship Modeling**
- Educational content is inherently hierarchical and interconnected
- Graph structure mirrors how educators think about curriculum (subjects contain units, units contain lessons)
- Relationships are first-class citizens, making connections explicit and queryable

**🚀 Powerful Traversals**
- Answer questions like "What are all lessons a Year 10 student studies?" with a single query
- Navigate from a lesson back to its subject, year group, and key stage effortlessly
- Discover learning pathways and prerequisite chains through relationship traversal

**🔄 Flexibility and Evolution**
- Easy to add new relationship types (e.g., "PREREQUISITE_FOR", "RELATES_TO")
- Schema can evolve without breaking existing queries
- Complex questions become simple queries (no complex JOINs needed)

**📊 Pattern Discovery**
- Identify curriculum gaps by analyzing relationship patterns
- Find central topics using graph algorithms (centrality measures)
- Discover natural groupings through community detection

### Target Audience

This documentation serves multiple audiences:

**👨‍🏫 Educators and Curriculum Planners**
- Use queries to build term plans and discover resources
- No technical background required for basic queries
- Practical examples focused on teaching scenarios

**📊 Educational Researchers and Analysts**
- Analyze curriculum structure and learning progressions
- Explore patterns in pedagogical design
- Generate insights about curriculum coverage

**💻 Developers and Data Engineers**
- Technical reference for integrating with the graph
- Performance optimization guidance
- Advanced query patterns and algorithms

**🎯 Educational Leadership**
- Understand curriculum organization at a high level
- Make data-driven decisions about curriculum design
- Identify opportunities for innovation

---

## 2. Executive Summary

### Graph Overview

The UK School Curriculum Knowledge Graph contains **16,891 nodes** and **25,684 relationships** representing the complete structure of the Oak National Academy curriculum. The graph models three interconnected hierarchies:

1. **Educational Structure:** Phase → Key Stage → Year
2. **Content Organization:** Subject → Unit → Lesson
3. **Qualification Pathways:** Exam Board/Tier → Programme → Unit Variant

These hierarchies intersect through "Unit Offerings" that connect specific year groups and subjects to curriculum units.

### Key Statistics

| Node Type | Count | Description |
|-----------|-------|-------------|
| **Lesson** | 12,631 | Individual teaching sessions with full pedagogical content |
| **Unitvariant** | 2,064 | Exam board-specific variants of curriculum units |
| **Unit** | 1,564 | Thematic collections of lessons (e.g., "Poetry anthology") |
| **Programme** | 258 | Exam board and year-specific qualification pathways |
| **Unitoffering** | 183 | Links between subjects, years, and units |
| **Thread** | 165 | Thematic learning strands across units |
| **Subject** | 22 | Core subjects (English, Maths, Science, etc.) |
| **Year** | 11 | Year groups from Year 1 to Year 11 |
| **Examboard** | 5 | AQA, Edexcel, Eduqas, OCR, WJEC |
| **Keystage** | 4 | KS1, KS2, KS3, KS4 |
| **Phase** | 2 | Primary and Secondary |
| **Tier** | 2 | Foundation and Higher |
| **Schemaversion** | 1 | Schema metadata |

### Primary Relationships

| Relationship | Count | Pattern | Meaning |
|--------------|-------|---------|---------|
| **HAS_LESSON** | 15,409 | `Unitvariant-[:HAS_LESSON]->Lesson` | Unit variants contain lessons |
| **HAS_UNITVARIANT** | 4,553 | `Programme/Unit-[:HAS_UNITVARIANT]->Unitvariant` | Units and programmes have variants |
| **HAS_THREAD** | 3,322 | `Unit-[:HAS_THREAD]->Thread` | Units belong to thematic threads |
| **HAS_UNIT** | 1,614 | `Unitoffering-[:HAS_UNIT]->Unit` | Offerings connect to units |
| **HAS_PROGRAMME** | 405 | `Examboard/Tier-[:HAS_PROGRAMME]->Programme` | Exam specs define programmes |
| **HAS_UNIT_OFFERING** | 366 | `Subject/Year-[:HAS_UNIT_OFFERING]->Unitoffering` | Subjects and years offer units |
| **HAS_YEAR** | 11 | `Keystage-[:HAS_YEAR]->Year` | Key stages contain year groups |
| **HAS_KEY_STAGE** | 4 | `Phase-[:HAS_KEY_STAGE]->Keystage` | Phases contain key stages |

### Quick Example

**Question:** "What lessons does a Year 10 English student study if they're taking the AQA exam?"

```cypher
// Find Year 10 English lessons for AQA programme
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(unit:Unit),
      (unit)-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (examboard:Examboard {examBoardSlug: "aqa"})-[:HAS_PROGRAMME]->(prog:Programme),
      (prog)-[:HAS_UNITVARIANT]->(uv),
      (uv)-[:HAS_LESSON]->(lesson:Lesson)
RETURN DISTINCT lesson.lessonTitle AS lesson, unit.unitTitle AS unit
LIMIT 10;
```

**Sample Results:**
| Lesson | Unit |
|--------|------|
| "Analysing how poets present relationships that change over time" | "Love and Relationships: poetry" |
| "Understanding the tone of Brontë's 'Mild the Mist Upon the Hill'" | "Belonging: poetry" |
| "Writing creatively about a theme: conflict" | "Conflict poetry: moving image" |

This single query traverses multiple relationships to answer a complex question about curriculum organization, demonstrating the power of the graph model.

---

## 3. Graph Schema Documentation

### 3.1 Visual Schema Diagram

```
                                    ┌──────────┐
                                    │  Phase   │
                                    │ (2 nodes)│
                                    └────┬─────┘
                                         │ HAS_KEY_STAGE
                                         ↓
                                    ┌────────────┐
                                    │  Keystage  │
                                    │ (4 nodes)  │
                                    └─────┬──────┘
                                          │ HAS_YEAR
                                          ↓
                    ┌─────────────────────────────────────┐
                    │              Year                   │
                    │           (11 nodes)                │
                    └──────────┬──────────────────────────┘
                               │
                               │ HAS_UNIT_OFFERING
                               ↓
                    ┌──────────────────────┐
  ┌──────────┐      │   Unitoffering       │      ┌──────────────┐
  │ Subject  │──────┤    (183 nodes)       │      │  Examboard   │
  │(22 nodes)│      └──────────┬───────────┘      │  (5 nodes)   │
  └──────────┘    HAS_UNIT_OFFERING │              └──────┬───────┘
       │                       │ HAS_UNIT                 │
       │                       ↓                          │ HAS_PROGRAMME
       │              ┌──────────────┐                    │
       │              │     Unit     │←───────┐           ↓
       │              │ (1,564 nodes)│        │    ┌──────────────┐
       │              └──┬────────┬──┘        │    │  Programme   │
       │                 │        │           │    │  (258 nodes) │
       │                 │        │HAS_THREAD │    └──────┬───────┘
       │      HAS_UNITVARIANT     ↓           │           │
       │                 │   ┌────────┐       │           │
       │                 │   │ Thread │       │      HAS_PROGRAMME
       │                 │   │(165)   │       │           │
       │                 ↓   └────────┘       │           ↓
       │         ┌─────────────────┐          │    ┌──────────┐
       │         │  Unitvariant    │←─────────┴────│   Tier   │
       │         │  (2,064 nodes)  │               │ (2 nodes)│
       │         └────────┬────────┘               └──────────┘
       │                  │ HAS_LESSON
       │                  ↓
       │          ┌───────────────┐
       └─────────→│    Lesson     │
                  │ (12,631 nodes)│
                  └───────────────┘

Legend:
  [Node] ──→ [Node]  : Relationship direction
  ↓                  : Hierarchical flow
```

### 3.2 Node Types

#### 3.2.1 Phase

**Description:** Represents the two major divisions of UK education.

**Cardinality:** 2 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `phaseId` | INTEGER | Unique identifier | `2`, `3` |
| `phaseSlug` | STRING | URL-friendly identifier | `"primary"`, `"secondary"` |
| `phaseTitle` | STRING | Display name | `"primary"`, `"secondary"` |
| `phaseDescription` | STRING | Full description | `"Primary"`, `"Secondary"` |
| `displayOrder` | INTEGER | Sort order | `2`, `3` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// Primary phase
{
  "phaseId": 2,
  "phaseSlug": "primary",
  "phaseTitle": "primary",
  "phaseDescription": "Primary",
  "displayOrder": 2
}

// Secondary phase
{
  "phaseId": 3,
  "phaseSlug": "secondary",
  "phaseTitle": "secondary",
  "phaseDescription": "Secondary",
  "displayOrder": 3
}
```

---

#### 3.2.2 Keystage

**Description:** UK Key Stages (KS1 through KS4) that organize the national curriculum.

**Cardinality:** 4 nodes (KS1, KS2, KS3, KS4)

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `keyStageId` | INTEGER | Unique identifier | `1`, `2`, `3`, `4` |
| `keyStageSlug` | STRING | URL-friendly identifier | `"ks1"`, `"ks2"`, `"ks3"`, `"ks4"` |
| `keyStageTitle` | STRING | Display name | `"KS1"`, `"KS2"`, `"KS3"`, `"KS4"` |
| `keyStageDescription` | STRING | Full description | `"Key Stage 1"`, `"Key Stage 2"`, etc. |
| `displayOrder` | INTEGER | Sort order | `2`, `3`, `4`, `5` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// Key Stage 4 (GCSE years)
{
  "keyStageId": 4,
  "keyStageSlug": "ks4",
  "keyStageTitle": "KS4",
  "keyStageDescription": "Key Stage 4",
  "displayOrder": 5
}

// Key Stage 3 (Secondary transition)
{
  "keyStageId": 3,
  "keyStageSlug": "ks3",
  "keyStageTitle": "KS3",
  "keyStageDescription": "Key Stage 3",
  "displayOrder": 4
}
```

---

#### 3.2.3 Year

**Description:** Individual year groups from Year 1 through Year 11.

**Cardinality:** 11 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `yearId` | INTEGER | Unique identifier | `10` |
| `yearSlug` | STRING | URL-friendly identifier | `"year-10"` |
| `yearTitle` | STRING | Display name | `"10"` |
| `yearDescription` | STRING | Full description | `"Year 10"` |
| `displayOrder` | INTEGER | Sort order | `11` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// Year 10 (GCSE year 1)
{
  "yearId": 10,
  "yearSlug": "year-10",
  "yearTitle": "10",
  "yearDescription": "Year 10",
  "displayOrder": 11
}

// Year 9 (End of KS3)
{
  "yearId": 9,
  "yearSlug": "year-9",
  "yearTitle": "9",
  "yearDescription": "Year 9",
  "displayOrder": 10
}
```

---

#### 3.2.4 Subject

**Description:** Academic subjects taught in the UK curriculum (English, Maths, Science, etc.).

**Cardinality:** 22 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `subjectId` | INTEGER | Unique identifier | `1`, `11`, `9` |
| `subjectSlug` | STRING | URL-friendly identifier | `"english"`, `"art"`, `"chemistry"` |
| `subjectTitle` | STRING | Display name | `"English"`, `"Art and design"` |
| `subjectDescription` | STRING (optional) | Key stage range or notes | `"KS4"`, `"EYFS, KS1, KS2, KS3"` |
| `subjectParentId` | INTEGER (optional) | Parent subject ID | `6` (Science parent for Chemistry) |
| `subjectParentTitle` | STRING (optional) | Parent subject name | `"Science"` |
| `displayOrder` | INTEGER | Sort order | `11`, `1`, `35` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// English (standalone subject)
{
  "subjectId": 1,
  "subjectSlug": "english",
  "subjectTitle": "English",
  "displayOrder": 11
}

// Chemistry (sub-subject of Science)
{
  "subjectId": 9,
  "subjectSlug": "chemistry",
  "subjectTitle": "Chemistry",
  "subjectDescription": "KS4",
  "subjectParentId": 6,
  "subjectParentTitle": "Science",
  "displayOrder": 35
}

// Art and design
{
  "subjectId": 11,
  "subjectSlug": "art",
  "subjectTitle": "Art and design",
  "displayOrder": 1
}
```

---

#### 3.2.5 Unitoffering

**Description:** Junction node connecting a specific Year and Subject to curriculum Units. Represents "Year 10 English offers these units."

**Cardinality:** 183 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `unitOfferingSlug` | STRING | Composite identifier | `"year-10-english"`, `"year-10-art"` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// Year 10 English offering
{
  "unitOfferingSlug": "year-10-english"
}

// Year 10 Chemistry offering
{
  "unitOfferingSlug": "year-10-chemistry"
}

// Year 10 Art offering
{
  "unitOfferingSlug": "year-10-art"
}
```

---

#### 3.2.6 Unit

**Description:** Thematic curriculum units containing lessons (e.g., "Poetry anthology: first study", "States of matter").

**Cardinality:** 1,564 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `unitId` | INTEGER | Unique identifier | `153`, `3748`, `1148` |
| `unitSlug` | STRING | URL-friendly identifier | `"poetry-anthology-first-study"` |
| `unitTitle` | STRING | Display name | `"Poetry anthology: first study"` |
| `unitDescription` | STRING | Full description | `"In this unit, pupils explore 11 of the 15 poems..."` |
| `whyThisWhyNow` | STRING (optional) | Pedagogical rationale | `"This unit uses and builds on pupils' understanding..."` |
| `priorKnowledge` | LIST OF STRING (optional) | Prerequisites | `["Pupils can use reading skills to decode texts.", ...]` |
| `subjectCategory` | LIST OF STRING (optional) | Subject area tags | `["Literature"]`, `["Chemistry"]` |
| `nullUnitVariantId` | INTEGER | Default variant ID | `927`, `4940` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instance:**
```cypher
{
  "unitId": 153,
  "unitSlug": "poetry-anthology-first-study",
  "unitTitle": "Poetry anthology: first study",
  "unitDescription": "In this unit, pupils explore 11 of the 15 poems from the Eduqas poetry anthology...",
  "whyThisWhyNow": "This unit uses and builds on pupils' understanding of comparative poetry analysis...",
  "priorKnowledge": [
    "Pupils can use reading skills to decode texts.",
    "Pupils can make clear inferences about texts.",
    "Pupils can comment on the language choices of a poet.",
    "Pupils can recognise and comment on some structural devices of poetry..."
  ],
  "subjectCategory": ["Literature"],
  "nullUnitVariantId": 927
}
```

---

#### 3.2.7 Unitvariant

**Description:** Exam board-specific variants of units (e.g., AQA version vs Edexcel version of poetry anthology).

**Cardinality:** 2,064 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `unitVariantId` | INTEGER | Unique identifier | `5071`, `203`, `201` |
| `optionTitle` | STRING | Variant display name | `"Poetry anthology (Assessment from summer 2027)"` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// AQA Poetry variant
{
  "unitVariantId": 5071,
  "optionTitle": "Poetry anthology (Assessment from summer 2027)"
}

// Edexcel Belonging variant
{
  "unitVariantId": 203,
  "optionTitle": "Belonging"
}

// AQA Love and Relationships variant
{
  "unitVariantId": 201,
  "optionTitle": "Love and Relationships"
}
```

---

#### 3.2.8 Lesson

**Description:** Individual teaching sessions with complete pedagogical content including keywords, learning points, misconceptions, and resources.

**Cardinality:** 12,631 nodes (largest node type)

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `lessonId` | INTEGER | Unique identifier | `29077`, `2537` |
| `lessonSlug` | STRING | URL-friendly identifier | `"analysing-extended-responses-to-the-eduqas-poetry-anthology"` |
| `lessonTitle` | STRING | Display name | `"Analysing extended responses to the Eduqas poetry anthology"` |
| `pupilLessonOutcome` | STRING | Learning objective | `"I can recognise excellent writing practice in a model response."` |
| `keywords` | LIST OF STRING | Key terms as JSON objects | `["{\"keyword\": \"nostalgia\", \"description\": \"...\"}", ...]` |
| `keyLearningPoints` | LIST OF STRING | Core concepts as JSON objects | `["{\"key_learning_point\": \"Analysing model answers...\"}", ...]` |
| `lessonOutline` | LIST OF STRING | Lesson structure as JSON | `["{\"lesson_outline\": \"Exploring model introductions\"}", ...]` |
| `misconceptionsMistakes` | LIST OF STRING | Common errors as JSON | `["{\"misconception\": \"...\", \"response\": \"...\"}", ...]` |
| `equipmentResources` | LIST OF STRING (optional) | Required materials | `["{\"equipment\": \"You will need a copy of...\"}", ...]` |
| `teacherTips` | LIST OF STRING (optional) | Teaching guidance | `["{\"teacher_tip\": \"If pupils have already...\"}", ...]` |
| `contentGuidance` | LIST OF STRING (optional) | Content warning codes | `["4"]`, `["2", "9"]` |
| `contentGuidanceDetails` | LIST OF STRING (optional) | Content warnings | `["{\"details\": \"This lesson contains references to grief...\"}", ...]` |
| `quizStarterId` | INTEGER | Starter quiz ID | `39436` |
| `quizExitId` | INTEGER | Exit quiz ID | `39437` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instance (abbreviated):**
```cypher
{
  "lessonId": 2537,
  "lessonSlug": "understanding-the-poem-mild-the-mist-upon-the-hill",
  "lessonTitle": "Understanding the tone of Brontë's 'Mild the Mist Upon the Hill'",
  "pupilLessonOutcome": "I can explain how Brontë creates tone in 'Mild the Mist Upon the Hill'.",
  "keywords": [
    "{\"keyword\": \"nostalgia\", \"description\": \"a feeling of pleasure and also slight sadness when you think about things that happened in the past\"}",
    "{\"keyword\": \"melancholic\", \"description\": \"expressing feelings of sadness\"}"
  ],
  "keyLearningPoints": [
    "{\"key_learning_point\": \"Like other Romantic poets, Brontë uses natural imagery to present human emotions.\"}",
    "{\"key_learning_point\": \"Some may argue Brontë's poem is about the sense of security and belonging her nostalgic memories bring.\"}"
  ],
  "contentGuidance": ["4"],
  "contentGuidanceDetails": ["{\"details\": \"This lesson contains references to grief and sadness.\"}"],
  "quizStarterId": 25435,
  "quizExitId": 25436
}
```

---

#### 3.2.9 Thread

**Description:** Thematic learning strands that span across units (e.g., "Modern literature strand 1: identity, belonging and community").

**Cardinality:** 165 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `threadId` | INTEGER | Unique identifier | `120`, `80`, `127` |
| `thread_slug` | STRING | URL-friendly identifier | `"modern-literature-strand-1-identity-belonging-and-community"` |
| `threadTitle` | STRING | Display name | `"Modern literature strand 1: identity, belonging and community"` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:55.085753"` |

**Example Instances:**
```cypher
// Thread 1: Identity
{
  "threadId": 120,
  "thread_slug": "modern-literature-strand-1-identity-belonging-and-community",
  "threadTitle": "Modern literature strand 1: identity, belonging and community"
}

// Thread 2: Power and control
{
  "threadId": 80,
  "thread_slug": "modern-literature-strand-2-power-control-and-oppressive-regimes",
  "threadTitle": "Modern literature strand 2: power, control and oppressive regimes"
}

// Thread 3: Poetry appreciation
{
  "threadId": 127,
  "thread_slug": "appreciation-of-poetry",
  "threadTitle": "Appreciation of poetry"
}
```

---

#### 3.2.10 Examboard

**Description:** UK exam boards that provide GCSE and A-Level qualifications.

**Cardinality:** 5 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `examBoardId` | INTEGER | Unique identifier | `1`, `2`, `5` |
| `examBoardSlug` | STRING | URL-friendly identifier | `"aqa"`, `"edexcel"`, `"eduqas"` |
| `examBoardTitle` | STRING | Display name | `"AQA"`, `"Edexcel"`, `"Eduqas"` |
| `examBoardDescription` | STRING | Full name | `"Assessment and Qualifications Alliance"` |
| `displayOrder` | INTEGER | Sort order | `1`, `2`, `5` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// AQA
{
  "examBoardId": 1,
  "examBoardSlug": "aqa",
  "examBoardTitle": "AQA",
  "examBoardDescription": "Assessment and Qualifications Alliance",
  "displayOrder": 1
}

// Edexcel
{
  "examBoardId": 2,
  "examBoardSlug": "edexcel",
  "examBoardTitle": "Edexcel",
  "examBoardDescription": "Edexcel",
  "displayOrder": 2
}

// Eduqas
{
  "examBoardId": 5,
  "examBoardSlug": "eduqas",
  "examBoardTitle": "Eduqas",
  "examBoardDescription": "Eduqas",
  "displayOrder": 5
}
```

---

#### 3.2.11 Tier

**Description:** GCSE qualification tiers (Foundation or Higher).

**Cardinality:** 2 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `tierId` | INTEGER | Unique identifier | `1`, `3` |
| `tierSlug` | STRING | URL-friendly identifier | `"foundation"`, `"higher"` |
| `tierTitle` | STRING | Display name | `"foundation"`, `"higher"` |
| `tierDescription` | STRING | Full description | `"Foundation"`, `"Higher"` |
| `displayOrder` | INTEGER | Sort order | `1`, `3` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// Foundation tier
{
  "tierId": 1,
  "tierSlug": "foundation",
  "tierTitle": "foundation",
  "tierDescription": "Foundation",
  "displayOrder": 1
}

// Higher tier
{
  "tierId": 3,
  "tierSlug": "higher",
  "tierTitle": "higher",
  "tierDescription": "Higher",
  "displayOrder": 3
}
```

---

#### 3.2.12 Programme

**Description:** Exam board and year-specific qualification pathways (e.g., "English Year 10 AQA").

**Cardinality:** 258 nodes

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `programmeSlug` | STRING | Composite identifier | `"english-secondary-year-10-aqa"` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:04.079946"` |

**Example Instances:**
```cypher
// Year 10 English AQA
{
  "programmeSlug": "english-secondary-year-10-aqa"
}

// Year 10 English Edexcel
{
  "programmeSlug": "english-secondary-year-10-edexcel"
}

// Year 10 English Eduqas
{
  "programmeSlug": "english-secondary-year-10-eduqas"
}
```

---

#### 3.2.13 Schemaversion

**Description:** Metadata node tracking the schema version.

**Cardinality:** 1 node

**Properties:**
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `schemaVersion` | STRING | Version identifier | `"v0.1.0-alpha"` |
| `schemaDescription` | STRING | Version notes | `"Schema design and experimentation."` |
| `isActive` | BOOLEAN | Active status | `true` |
| `lastUpdated` | STRING | Timestamp | `"2025-10-08T22:27:24.364749"` |

**Example Instance:**
```cypher
{
  "schemaVersion": "v0.1.0-alpha",
  "schemaDescription": "Schema design and experimentation.",
  "isActive": true,
  "lastUpdated": "2025-10-08T22:27:24.364749"
}
```

---

### 3.3 Relationship Types

#### 3.3.1 HAS_KEY_STAGE

**Description:** Links Phase nodes to their constituent Key Stages.

**Pattern:** `(Phase)-[:HAS_KEY_STAGE]->(Keystage)`

**Cardinality:** 4 relationships

**Properties:** None

**Semantics:** Indicates that a Phase (Primary or Secondary) contains specific Key Stages. For example, Primary phase contains KS1 and KS2, while Secondary contains KS3 and KS4.

**Example Query:**
```cypher
// Find all key stages in the secondary phase
MATCH (p:Phase {phaseSlug: "secondary"})-[:HAS_KEY_STAGE]->(ks:Keystage)
RETURN ks.keyStageTitle AS keyStage, ks.keyStageDescription AS description
ORDER BY ks.displayOrder;
```

**Sample Results:**
| keyStage | description |
|----------|-------------|
| KS3 | Key Stage 3 |
| KS4 | Key Stage 4 |

---

#### 3.3.2 HAS_YEAR

**Description:** Links Key Stage nodes to their constituent Year groups.

**Pattern:** `(Keystage)-[:HAS_YEAR]->(Year)`

**Cardinality:** 11 relationships

**Properties:** None

**Semantics:** Indicates that a Key Stage contains specific Year groups. For example, KS4 contains Years 10 and 11 (GCSE years).

**Example Query:**
```cypher
// Find all years in Key Stage 4
MATCH (ks:Keystage {keyStageSlug: "ks4"})-[:HAS_YEAR]->(y:Year)
RETURN y.yearTitle AS year, y.yearDescription AS description
ORDER BY y.displayOrder;
```

**Sample Results:**
| year | description |
|------|-------------|
| 10 | Year 10 |
| 11 | Year 11 |

---

#### 3.3.3 HAS_UNIT_OFFERING

**Description:** Links Subject and Year nodes to Unitoffering junction nodes.

**Pattern:**
- `(Subject)-[:HAS_UNIT_OFFERING]->(Unitoffering)`
- `(Year)-[:HAS_UNIT_OFFERING]->(Unitoffering)`

**Cardinality:** 366 relationships (183 from Subject, 183 from Year)

**Properties:** None

**Semantics:** Creates the connection between a specific Year group and Subject to available curriculum Units. A Unitoffering represents "Year X studying Subject Y has access to these units."

**Example Query:**
```cypher
// Find unit offerings for Year 10 English
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo)
RETURN uo.unitOfferingSlug AS offering;
```

**Sample Result:**
| offering |
|----------|
| year-10-english |

---

#### 3.3.4 HAS_UNIT

**Description:** Links Unitoffering nodes to the actual Unit nodes they provide.

**Pattern:** `(Unitoffering)-[:HAS_UNIT]->(Unit)`

**Cardinality:** 1,614 relationships

**Properties:** None

**Semantics:** Indicates that a Unit Offering (Year + Subject combination) provides access to specific curriculum Units.

**Example Query:**
```cypher
// Find all units available for Year 10 English
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(unit:Unit)
RETURN DISTINCT unit.unitTitle AS unit
LIMIT 5;
```

**Sample Results:**
| unit |
|------|
| Poetry anthology: first study |
| Love and Relationships: poetry |
| Belonging: poetry |

---

#### 3.3.5 HAS_UNITVARIANT

**Description:** Links Unit and Programme nodes to their exam board-specific variants.

**Pattern:**
- `(Unit)-[:HAS_UNITVARIANT]->(Unitvariant)`
- `(Programme)-[:HAS_UNITVARIANT]->(Unitvariant)`

**Cardinality:** 4,553 relationships (2,064 from Unit, 2,489 from Programme)

**Properties:** None

**Semantics:** Indicates that a Unit or Programme has specific exam board variants. Different exam boards may have different versions of the same conceptual unit.

**Example Query:**
```cypher
// Find all variants of a specific unit
MATCH (unit:Unit {unitSlug: "poetry-anthology-first-study"})-[:HAS_UNITVARIANT]->(uv:Unitvariant)
RETURN uv.optionTitle AS variant
LIMIT 3;
```

**Sample Results:**
| variant |
|---------|
| Poetry anthology (Assessment from summer 2027) |
| Love and Relationships |
| Belonging |

---

#### 3.3.6 HAS_LESSON

**Description:** Links Unitvariant nodes to the Lesson nodes they contain.

**Pattern:** `(Unitvariant)-[:HAS_LESSON]->(Lesson)`

**Cardinality:** 15,409 relationships (largest relationship type)

**Properties:** None

**Semantics:** Indicates that a Unit Variant contains specific lessons. This is the primary relationship for accessing teaching content.

**Example Query:**
```cypher
// Find lessons in a specific unit variant
MATCH (uv:Unitvariant {optionTitle: "Love and Relationships"})-[:HAS_LESSON]->(lesson:Lesson)
RETURN lesson.lessonTitle AS lesson, lesson.pupilLessonOutcome AS outcome
LIMIT 3;
```

**Sample Results:**
| lesson | outcome |
|--------|---------|
| Analysing how poets present relationships that change over time | I can write a comparative analysis of 'Walking Away' and one other poem. |

---

#### 3.3.7 HAS_THREAD

**Description:** Links Unit nodes to thematic Thread nodes.

**Pattern:** `(Unit)-[:HAS_THREAD]->(Thread)`

**Cardinality:** 3,322 relationships

**Properties:** None

**Semantics:** Indicates that a Unit belongs to one or more thematic learning threads. Threads provide cross-unit thematic organization.

**Example Query:**
```cypher
// Find all threads for a unit
MATCH (unit:Unit {unitSlug: "poetry-anthology-first-study"})-[:HAS_THREAD]->(thread:Thread)
RETURN thread.threadTitle AS theme;
```

**Sample Results:**
| theme |
|-------|
| Appreciation of poetry |
| Modern literature strand 1: identity, belonging and community |

---

#### 3.3.8 HAS_PROGRAMME

**Description:** Links Examboard and Tier nodes to Programme nodes.

**Pattern:**
- `(Examboard)-[:HAS_PROGRAMME]->(Programme)`
- `(Tier)-[:HAS_PROGRAMME]->(Programme)`

**Cardinality:** 405 relationships (95 from Examboard, 52 from Tier, 258 from Unitoffering)

**Properties:** None

**Semantics:** Indicates that an Exam Board or Tier provides specific qualification programmes. Programmes are exam board and year-specific pathways.

**Example Query:**
```cypher
// Find all AQA programmes
MATCH (eb:Examboard {examBoardSlug: "aqa"})-[:HAS_PROGRAMME]->(prog:Programme)
RETURN prog.programmeSlug AS programme
LIMIT 5;
```

**Sample Results:**
| programme |
|-----------|
| english-secondary-year-10-aqa |
| english-secondary-year-11-aqa |
| maths-secondary-year-10-aqa |

---

## 4. Data Model Deep Dive

### Curriculum Structure

The UK School Curriculum Knowledge Graph models a complex, multi-layered educational structure. Understanding how these layers interact is key to effectively querying the graph.

#### Three Primary Hierarchies

**1. Educational Structure Hierarchy** (Phase → Key Stage → Year)
```
Phase (Primary/Secondary)
    ↓
Key Stage (KS1, KS2, KS3, KS4)
    ↓
Year (Year 1-11)
```

This hierarchy represents the organizational structure of UK education:
- **Phase** divides education into Primary (ages 5-11) and Secondary (ages 11-16+)
- **Key Stage** groups years for curriculum planning (KS1: Years 1-2, KS2: Years 3-6, KS3: Years 7-9, KS4: Years 10-11)
- **Year** represents individual year groups

**2. Content Organization Hierarchy** (Subject → Unit → Lesson)
```
Subject (English, Maths, Science, etc.)
    ↓
Unit (Thematic collections)
    ↓  
Lesson (Individual teaching sessions)
```

This hierarchy organizes the actual teaching content:
- **Subject** represents academic disciplines
- **Unit** groups related lessons thematically (e.g., "Poetry anthology", "States of matter")
- **Lesson** contains the detailed pedagogical content for a single teaching session

**3. Qualification Pathway Hierarchy** (Exam Board → Programme → Unit Variant → Lesson)
```
Exam Board (AQA, Edexcel, etc.) + Tier (Foundation/Higher)
    ↓
Programme (Subject + Year + Exam Board combination)
    ↓
Unit Variant (Exam board-specific unit version)
    ↓
Lesson (Shared or variant-specific)
```

This hierarchy models exam qualifications:
- **Exam Board** and **Tier** define the qualification provider and difficulty level
- **Programme** represents a specific qualification pathway (e.g., "Year 10 English AQA")
- **Unit Variant** provides exam board-specific versions of units
- **Lesson** content may be shared across variants or specific to one

### Hierarchical Relationships

#### The Unitoffering Junction Pattern

The **Unitoffering** node is crucial for connecting the educational hierarchy to content:

```cypher
// How Year and Subject connect to Units
MATCH path = (year:Year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject),
             (uo)-[:HAS_UNIT]->(unit:Unit)
WHERE year.yearTitle = "10" AND subject.subjectSlug = "english"
RETURN path;
```

This pattern shows:
1. A **Year** and **Subject** both connect to the same **Unitoffering**
2. The **Unitoffering** acts as a junction, representing "Year 10 English"
3. The **Unitoffering** then connects to multiple **Units** available for that year/subject combination

**Why this pattern?**
- Allows units to be offered to multiple year/subject combinations
- Enables flexible curriculum organization
- Supports reuse of units across different contexts

#### From Educational Level to Lessons

The complete path from educational structure to lessons:

```cypher
// Trace from Phase to Lesson
MATCH path = (phase:Phase)-[:HAS_KEY_STAGE]->(ks:Keystage)-[:HAS_YEAR]->(year:Year),
             (year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
             (subject:Subject)-[:HAS_UNIT_OFFERING]->(uo),
             (uo)-[:HAS_UNIT]->(unit:Unit),
             (unit)-[:HAS_UNITVARIANT]->(uv:Unitvariant),
             (uv)-[:HAS_LESSON]->(lesson:Lesson)
WHERE phase.phaseSlug = "secondary" 
  AND subject.subjectSlug = "english"
  AND year.yearTitle = "10"
RETURN path
LIMIT 1;
```

This query demonstrates the full traversal from educational structure to specific lessons.

### Cross-Cutting Relationships

#### Thematic Threads

**Threads** provide cross-unit thematic organization:

```cypher
// Find all units in a thematic thread
MATCH (thread:Thread {threadTitle: "Appreciation of poetry"})<-[:HAS_THREAD]-(unit:Unit)
RETURN unit.unitTitle AS unit, unit.subjectCategory AS category
ORDER BY unit.unitTitle
LIMIT 5;
```

**Purpose of Threads:**
- Connect related units across different year groups
- Enable curriculum coherence and progression
- Support cross-curricular planning

#### Exam Board Variants

Units can have multiple variants for different exam boards:

```cypher
// Compare variants of the same unit
MATCH (unit:Unit {unitSlug: "poetry-anthology-first-study"})-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (prog:Programme)-[:HAS_UNITVARIANT]->(uv),
      (eb:Examboard)-[:HAS_PROGRAMME]->(prog)
RETURN eb.examBoardTitle AS examBoard, 
       uv.optionTitle AS variant,
       count{(uv)-[:HAS_LESSON]->(:Lesson)} AS lessonCount
ORDER BY examBoard
LIMIT 5;
```

This shows how the same conceptual unit (e.g., poetry anthology) has different implementations for AQA, Edexcel, and Eduqas exam boards.

#### Subject Hierarchies

Some subjects have parent-child relationships:

```cypher
// Find all science sub-subjects
MATCH (parent:Subject {subjectTitle: "Science"})<-[:subjectParentId]-(child:Subject)
RETURN child.subjectTitle AS subject, child.subjectDescription AS keyStages
ORDER BY child.displayOrder;
```

Example: Biology, Chemistry, and Physics are children of the Science subject.

### Data Patterns and Design Decisions

**💡 Key Design Patterns:**

1. **Junction Nodes** (Unitoffering, Programme)
   - Enable many-to-many relationships
   - Represent logical combinations (Year + Subject, Exam Board + Subject)

2. **Variant Pattern** (Unitvariant)
   - Same conceptual unit, different exam board implementations
   - Shared where possible, specialized where necessary

3. **Hierarchical Decomposition**
   - Educational structure separate from content
   - Both converge at Unit level

4. **Rich Metadata on Leaves**
   - Lesson nodes contain most detailed information
   - Higher-level nodes focus on organization

5. **Slug-based Identifiers**
   - URL-friendly identifiers for all entities
   - Enables web integration and human-readable references

---

## 5. Getting Started

### 5.1 Connection Information

**Neo4j Database Connection:**
```
URI: bolt://localhost:7687 (or your Neo4j AuraDB URI)
Database: neo4j (default)
Username: neo4j
Password: [your-password]
```

**Accessing the Database:**

1. **Neo4j Browser:**
   - Navigate to http://localhost:7474 (for local) or your AuraDB URL
   - Enter credentials
   - Use the query editor to run Cypher queries

2. **Neo4j Desktop:**
   - Open your database in Neo4j Desktop
   - Click "Open Browser" or "Explore"
   - Run queries in the integrated browser

3. **Python (neo4j driver):**
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    result = session.run("MATCH (n:Lesson) RETURN count(n) AS lessonCount")
    print(result.single()["lessonCount"])
```

4. **Cypher Shell (CLI):**
```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p password
```

### 5.2 Basic Query Examples

#### Example 1: Count All Nodes

```cypher
// Count nodes by type
CALL db.labels() YIELD label
CALL {
  WITH label
  MATCH (n) WHERE label IN labels(n)
  RETURN count(n) as count
}
RETURN label, count
ORDER BY count DESC;
```

**Purpose:** Get an overview of the graph's composition.

**Expected Results:**
| label | count |
|-------|-------|
| Lesson | 12,631 |
| Unitvariant | 2,064 |
| Unit | 1,564 |
| ... | ... |

---

#### Example 2: List All Subjects

```cypher
// Find all subjects
MATCH (s:Subject)
RETURN s.subjectTitle AS subject, 
       s.subjectDescription AS description,
       s.subjectParentTitle AS parentSubject
ORDER BY s.displayOrder;
```

**Purpose:** See what subjects are available in the curriculum.

**Expected Results:**
| subject | description | parentSubject |
|---------|-------------|---------------|
| Art and design | null | null |
| English | null | null |
| Chemistry | KS4 | Science |
| ... | ... | ... |

---

#### Example 3: Find Units for a Subject

```cypher
// Find all English units
MATCH (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (uo)-[:HAS_UNIT]->(unit:Unit)
RETURN DISTINCT unit.unitTitle AS unit, unit.unitDescription AS description
ORDER BY unit.unitTitle
LIMIT 5;
```

**Purpose:** Explore available units for a specific subject.

**Expected Results:**
| unit | description |
|------|-------------|
| Belonging: poetry | In this unit, pupils explore... |
| Love and Relationships: poetry | In this unit, pupils explore... |
| Poetry anthology: first study | In this unit, pupils explore... |

---

#### Example 4: Find Lessons in a Unit

```cypher
// Find lessons in a specific unit
MATCH (unit:Unit {unitSlug: "states-of-matter"})-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (uv)-[:HAS_LESSON]->(lesson:Lesson)
RETURN lesson.lessonTitle AS lesson,
       lesson.pupilLessonOutcome AS outcome
ORDER BY lesson.lessonTitle
LIMIT 5;
```

**Purpose:** See the lessons within a curriculum unit.

**Expected Results:**
| lesson | outcome |
|--------|---------|
| Changes of state | I can explain changes of state in terms of particles |
| Particle model | I can describe the particle model |
| ... | ... |

---

#### Example 5: Find Year Groups for a Key Stage

```cypher
// Find all years in KS4
MATCH (ks:Keystage {keyStageSlug: "ks4"})-[:HAS_YEAR]->(year:Year)
RETURN year.yearTitle AS year, year.yearDescription AS description
ORDER BY year.displayOrder;
```

**Purpose:** Understand the structure of key stages.

**Expected Results:**
| year | description |
|------|-------------|
| 10 | Year 10 |
| 11 | Year 11 |

---

#### Example 6: Find Lessons by Keyword

```cypher
// Find lessons containing a specific keyword
MATCH (lesson:Lesson)
WHERE any(keyword IN lesson.keywords WHERE keyword CONTAINS 'Romantic')
RETURN lesson.lessonTitle AS lesson,
       lesson.pupilLessonOutcome AS outcome,
       lesson.keywords[0..2] AS sampleKeywords
LIMIT 5;
```

**Purpose:** Search for lessons by pedagogical content.

**Expected Results:**
| lesson | outcome | sampleKeywords |
|--------|---------|----------------|
| Understanding the tone of Brontë's 'Mild the Mist Upon the Hill' | I can explain how Brontë creates tone... | ["{\"keyword\": \"Romanticism\", ...}", ...] |

---

#### Example 7: Get Complete Lesson Details

```cypher
// Get full details for a lesson
MATCH (lesson:Lesson {lessonSlug: "understanding-the-poem-mild-the-mist-upon-the-hill"})
RETURN lesson.lessonTitle AS title,
       lesson.pupilLessonOutcome AS outcome,
       lesson.keywords AS keywords,
       lesson.keyLearningPoints AS learningPoints,
       lesson.misconceptionsMistakes AS misconceptions,
       lesson.equipmentResources AS equipment;
```

**Purpose:** Access complete pedagogical content for a lesson.

---

## 6. Common Query Patterns

### 6.1 Curriculum Navigation

#### Pattern 1: Find All Content for a Year Group

**Use Case:** "What does a Year 10 student study?"

```cypher
// List all subjects and units for Year 10
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject)-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(unit:Unit)
RETURN subject.subjectTitle AS subject,
       count(DISTINCT unit) AS unitCount,
       collect(DISTINCT unit.unitTitle)[0..3] AS sampleUnits
ORDER BY subject.subjectTitle;
```

**Results Interpretation:**
Shows the breadth of curriculum for Year 10, grouped by subject.

---

#### Pattern 2: Navigate Unit Hierarchy

**Use Case:** "Show me the structure from subject down to lessons for a specific topic"

```cypher
// Explore the hierarchy for a subject
MATCH (subject:Subject {subjectSlug: "chemistry"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (uo)-[:HAS_UNIT]->(unit:Unit),
      (unit)-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (uv)-[:HAS_LESSON]->(lesson:Lesson)
WHERE unit.unitSlug = "states-of-matter"
RETURN subject.subjectTitle AS subject,
       unit.unitTitle AS unit,
       uv.optionTitle AS variant,
       count(lesson) AS lessonCount,
       collect(lesson.lessonTitle)[0..3] AS sampleLessons;
```

**Results Interpretation:**
Shows the complete path from subject to lessons with counts.

---

#### Pattern 3: Find Prerequisites for a Unit

**Use Case:** "What prior knowledge do students need for this unit?"

```cypher
// Get prerequisite knowledge for a unit
MATCH (unit:Unit {unitSlug: "poetry-anthology-first-study"})
RETURN unit.unitTitle AS unit,
       unit.priorKnowledge AS prerequisites,
       unit.whyThisWhyNow AS pedagogicalRationale
LIMIT 1;
```

**Results Interpretation:**
Returns structured prior knowledge requirements and pedagogical context.

---

### 6.2 Relationship Traversal

#### Pattern 4: Exam Board Comparison

**Use Case:** "Compare how different exam boards approach the same topic"

```cypher
// Compare exam board variants for a unit
MATCH (unit:Unit {unitSlug: "poetry-anthology-first-study"})-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (prog:Programme)-[:HAS_UNITVARIANT]->(uv),
      (eb:Examboard)-[:HAS_PROGRAMME]->(prog)
RETURN eb.examBoardTitle AS examBoard,
       uv.optionTitle AS variant,
       count{(uv)-[:HAS_LESSON]->(:Lesson)} AS lessonCount
ORDER BY examBoard;
```

**Results Interpretation:**
Shows how exam boards differ in their treatment of the same conceptual unit.

---

#### Pattern 5: Thematic Connections

**Use Case:** "Find all units connected by a theme"

```cypher
// Explore units in a thematic thread
MATCH (thread:Thread)-[:HAS_THREAD]-(unit:Unit)
WHERE thread.threadTitle CONTAINS 'poetry'
RETURN thread.threadTitle AS theme,
       collect(DISTINCT unit.unitTitle) AS relatedUnits,
       count(DISTINCT unit) AS unitCount
ORDER BY unitCount DESC
LIMIT 5;
```

**Results Interpretation:**
Reveals thematic connections across the curriculum.

---

#### Pattern 6: Subject to Lesson Path

**Use Case:** "Find the quickest path from a subject to its lessons"

```cypher
// Direct path from subject to lessons
MATCH (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(:Unitoffering)-[:HAS_UNIT]->(:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
RETURN lesson.lessonTitle AS lesson, 
       lesson.pupilLessonOutcome AS outcome
ORDER BY lesson.lessonTitle
LIMIT 10;
```

**Results Interpretation:**
Direct traversal showing all accessible lessons for a subject.

---

### 6.3 Analysis Queries

#### Pattern 7: Curriculum Coverage Analysis

**Use Case:** "Which subjects have the most curriculum content?"

```cypher
// Analyze curriculum breadth by subject
MATCH (subject:Subject)-[:HAS_UNIT_OFFERING]->(:Unitoffering)-[:HAS_UNIT]->(unit:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
RETURN subject.subjectTitle AS subject,
       count(DISTINCT unit) AS units,
       count(DISTINCT lesson) AS lessons,
       avg(size(lesson.keyLearningPoints)) AS avgLearningPointsPerLesson
ORDER BY lessons DESC
LIMIT 10;
```

**Results Interpretation:**
Quantifies curriculum coverage by subject with learning point density.

---

#### Pattern 8: Find Content Gaps

**Use Case:** "Which year groups have limited content for a subject?"

```cypher
// Find year/subject combinations with few units
MATCH (year:Year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject),
      (uo)-[:HAS_UNIT]->(unit:Unit)
WITH year, subject, count(unit) AS unitCount
WHERE unitCount < 3
RETURN year.yearDescription AS year,
       subject.subjectTitle AS subject,
       unitCount
ORDER BY unitCount, year.yearTitle;
```

**Results Interpretation:**
Identifies potential curriculum gaps requiring attention.

---

#### Pattern 9: Lesson Complexity Analysis

**Use Case:** "Which lessons have the most pedagogical scaffolding?"

```cypher
// Analyze lesson complexity
MATCH (lesson:Lesson)
RETURN lesson.lessonTitle AS lesson,
       size(lesson.keywords) AS keywordCount,
       size(lesson.keyLearningPoints) AS learningPointCount,
       size(lesson.misconceptionsMistakes) AS misconceptionCount,
       size(lesson.keywords) + size(lesson.keyLearningPoints) + size(lesson.misconceptionsMistakes) AS totalComplexity
ORDER BY totalComplexity DESC
LIMIT 10;
```

**Results Interpretation:**
Identifies lessons with rich pedagogical content.

---

#### Pattern 10: Cross-Curricular Opportunities

**Use Case:** "Find topics that appear in multiple subjects"

```cypher
// Find threads that span multiple subjects
MATCH (thread:Thread)-[:HAS_THREAD]-(unit:Unit)<-[:HAS_UNIT]-(:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject)
WITH thread, collect(DISTINCT subject.subjectTitle) AS subjects
WHERE size(subjects) > 1
RETURN thread.threadTitle AS theme,
       subjects,
       size(subjects) AS subjectCount
ORDER BY subjectCount DESC
LIMIT 10;
```

**Results Interpretation:**
Reveals opportunities for cross-curricular teaching.

---

## 7. Practical Use Cases

This section provides real-world scenarios with complete query examples, actual results, and interpretations.

### Use Case 1: Building a Year 10 English Term Plan

**Scenario:** A head of English needs to plan Term 1 for Year 10 students studying the AQA exam board. They want to see all available units and their lesson counts to allocate teaching time.

**Query:**
```cypher
// Find all Year 10 English units for AQA with lesson counts
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(unit:Unit),
      (unit)-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (examboard:Examboard {examBoardSlug: "aqa"})-[:HAS_PROGRAMME]->(prog:Programme),
      (prog)-[:HAS_UNITVARIANT]->(uv)
WITH unit, uv, count{(uv)-[:HAS_LESSON]->(:Lesson)} AS lessonCount
RETURN unit.unitTitle AS unit,
       uv.optionTitle AS variant,
       lessonCount,
       unit.whyThisWhyNow AS rationale
ORDER BY unit.unitTitle;
```

**Results:**
| unit | variant | lessonCount | rationale |
|------|---------|-------------|-----------|
| Love and Relationships: poetry | Love and Relationships | 15 | This unit builds on prior poetry analysis skills... |
| Poetry anthology: first study | Poetry anthology (Assessment from summer 2027) | 22 | This unit uses and builds on pupils' understanding of comparative poetry analysis... |

**Interpretation:**
The teacher can see that the Poetry anthology unit has 22 lessons (roughly 11 weeks at 2 lessons/week), making it suitable for a full term. The rationale helps justify the sequencing decision.

**Query Variations:**
- Change `examBoardSlug` to "edexcel" or "eduqas" for different exam boards
- Add `WHERE lessonCount >= 10` to filter for substantial units only
- Add threading information to see thematic connections

---

### Use Case 2: Finding Lessons with Specific Learning Prerequisites

**Scenario:** A teacher wants to find all Chemistry lessons that require students to understand the particle model, to ensure proper sequencing.

**Query:**
```cypher
// Find lessons with specific prerequisite knowledge
MATCH (subject:Subject {subjectSlug: "chemistry"})-[:HAS_UNIT_OFFERING]->(:Unitoffering)-[:HAS_UNIT]->(unit:Unit),
      (unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
WHERE any(prereq IN unit.priorKnowledge WHERE prereq CONTAINS 'particle model')
RETURN unit.unitTitle AS unit,
       lesson.lessonTitle AS lesson,
       lesson.pupilLessonOutcome AS outcome,
       unit.priorKnowledge AS prerequisites
ORDER BY unit.unitTitle, lesson.lessonTitle
LIMIT 10;
```

**Results:**
| unit | lesson | outcome | prerequisites |
|------|--------|---------|---------------|
| States of matter | Changes of state | I can explain changes of state in terms of particles | ["The particle model shows how solids, liquids and gases are organised together", ...] |
| States of matter | Particle model | I can describe the particle model | ["The particle model shows how solids, liquids and gases are organised together", ...] |

**Interpretation:**
These lessons build directly on particle model knowledge, so they should be taught after students have mastered that foundation.

**Query Variations:**
- Change the prerequisite search term to find other knowledge dependencies
- Add lesson counts per unit to prioritize teaching order
- Include `unit.whyThisWhyNow` to understand pedagogical progression

---

### Use Case 3: Identifying Cross-Curricular Teaching Opportunities

**Scenario:** The school wants to plan a cross-curricular week on "Identity and Community" and needs to find relevant content across all subjects.

**Query:**
```cypher
// Find units with identity/community themes across subjects
MATCH (thread:Thread)-[:HAS_THREAD]-(unit:Unit)<-[:HAS_UNIT]-(:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject)
WHERE thread.threadTitle CONTAINS 'identity' OR thread.threadTitle CONTAINS 'community'
WITH thread, subject, unit
RETURN thread.threadTitle AS theme,
       subject.subjectTitle AS subject,
       collect(unit.unitTitle) AS units,
       count(unit) AS unitCount
ORDER BY subject.subjectTitle;
```

**Results:**
| theme | subject | units | unitCount |
|-------|---------|-------|-----------|
| Modern literature strand 1: identity, belonging and community | English | ["Poetry anthology: first study", "Modern texts: identity"] | 2 |
| Modern literature strand 1: identity, belonging and community | History | ["Migration and identity in Britain"] | 1 |

**Interpretation:**
English and History both have units on this theme, creating an opportunity for collaborative teaching. Teachers can coordinate timing and share student work across subjects.

**Query Variations:**
- Search for other themes like "power", "conflict", or "environment"
- Add year group filters to find age-appropriate cross-curricular content
- Include lesson counts to estimate teaching time commitment

---

### Use Case 4: Analyzing Exam Board Differences

**Scenario:** The school is considering switching from AQA to Edexcel and wants to understand how the poetry curriculum differs between exam boards.

**Query:**
```cypher
// Compare poetry units across exam boards
MATCH (unit:Unit)-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (prog:Programme)-[:HAS_UNITVARIANT]->(uv),
      (eb:Examboard)-[:HAS_PROGRAMME]->(prog)
WHERE unit.unitTitle CONTAINS 'poetry' OR unit.unitTitle CONTAINS 'Poetry'
WITH eb, unit, uv, count{(uv)-[:HAS_LESSON]->(:Lesson)} AS lessons
RETURN eb.examBoardTitle AS examBoard,
       unit.unitTitle AS unit,
       uv.optionTitle AS variant,
       lessons
ORDER BY unit.unitTitle, examBoard;
```

**Results:**
| examBoard | unit | variant | lessons |
|-----------|------|---------|---------|
| AQA | Poetry anthology: first study | Love and Relationships | 15 |
| Edexcel | Poetry anthology: first study | Belonging | 18 |
| Eduqas | Poetry anthology: first study | Poetry anthology (Assessment from summer 2027) | 22 |

**Interpretation:**
Eduqas has the most comprehensive poetry anthology (22 lessons vs 15-18 for others), suggesting more detailed coverage. The different variant names indicate different poem selections.

**Query Variations:**
- Compare specific units by adding `WHERE unit.unitSlug = 'specific-unit'`
- Add `unit.whyThisWhyNow` to compare pedagogical approaches
- Include keyword analysis to see content focus differences

---

### Use Case 5: Finding Lessons by Content Warning

**Scenario:** A teacher needs to prepare parents for sensitive content and wants to find all Year 10 English lessons that contain references to grief or loss.

**Query:**
```cypher
// Find lessons with specific content warnings
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
WHERE any(detail IN lesson.contentGuidanceDetails WHERE detail CONTAINS 'grief' OR detail CONTAINS 'sadness')
RETURN lesson.lessonTitle AS lesson,
       lesson.contentGuidanceDetails AS contentWarnings,
       lesson.pupilLessonOutcome AS outcome
ORDER BY lesson.lessonTitle;
```

**Results:**
| lesson | contentWarnings | outcome |
|--------|-----------------|---------|
| Understanding the tone of Brontë's 'Mild the Mist Upon the Hill' | ["{\"details\": \"This lesson contains references to grief and sadness.\"}"] | I can explain how Brontë creates tone in 'Mild the Mist Upon the Hill'. |

**Interpretation:**
This lesson requires advance notice to parents due to sensitive themes. The teacher can plan appropriate support and alternative materials if needed.

**Query Variations:**
- Search for other content types: "violence", "prejudice", "death"
- Add unit context to see thematic clustering of sensitive content
- Include `teacherTips` to access guidance for handling sensitive topics

---

### Use Case 6: Creating a Learning Progression Map

**Scenario:** A curriculum designer wants to map how poetry analysis skills develop from Year 7 through Year 10.

**Query:**
```cypher
// Track poetry units across year groups
MATCH (year:Year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(unit:Unit)
WHERE unit.unitTitle CONTAINS 'poetry' OR unit.unitTitle CONTAINS 'Poetry'
WITH year, unit
ORDER BY year.yearId, unit.unitTitle
RETURN year.yearTitle AS year,
       collect(unit.unitTitle) AS poetryUnits,
       collect(unit.whyThisWhyNow)[0] AS sampleRationale
ORDER BY year.yearId;
```

**Results:**
| year | poetryUnits | sampleRationale |
|------|-------------|-----------------|
| 7 | ["Introduction to poetry"] | This unit introduces fundamental poetry analysis skills... |
| 9 | ["Poetry: conflict themes"] | This unit builds on Year 7-8 skills by introducing thematic comparison... |
| 10 | ["Poetry anthology: first study", "Love and Relationships: poetry"] | This unit uses and builds on pupils' understanding of comparative poetry analysis... |

**Interpretation:**
The progression shows increasing complexity: Year 7 introduces basics, Year 9 adds thematic analysis, Year 10 focuses on exam-level comparative work. This validates the curriculum design.

**Query Variations:**
- Filter by `unit.priorKnowledge` to see explicit skill dependencies
- Add lesson counts to see depth of coverage at each level
- Include threads to map thematic progression

---

### Use Case 7: Finding Lessons for Differentiation

**Scenario:** A teacher wants to find Foundation and Higher tier versions of the same topic to support differentiated teaching in a mixed-ability class.

**Query:**
```cypher
// Compare Foundation and Higher tier content
MATCH (tier:Tier)-[:HAS_PROGRAMME]->(prog:Programme),
      (prog)-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (unit:Unit)-[:HAS_UNITVARIANT]->(uv)
WHERE unit.unitTitle CONTAINS 'States of matter'
WITH tier, unit, uv, count{(uv)-[:HAS_LESSON]->(:Lesson)} AS lessons
RETURN tier.tierTitle AS tier,
       unit.unitTitle AS unit,
       lessons,
       uv.optionTitle AS variant
ORDER BY tier.tierTitle, unit.unitTitle;
```

**Results:**
| tier | unit | lessons | variant |
|------|------|---------|---------|
| foundation | States of matter | 8 | Foundation Chemistry |
| higher | States of matter | 12 | Higher Chemistry |

**Interpretation:**
Higher tier has 4 additional lessons, likely covering more complex concepts. The teacher can use foundation lessons for core content and higher tier extensions for advanced students.

**Query Variations:**
- Add lesson details to identify which topics are tier-specific
- Compare `keyLearningPoints` to see complexity differences
- Include `misconceptionsMistakes` to see common errors at each level

---

### Use Case 8: Planning Assessment Preparation

**Scenario:** An exam coordinator needs to identify all Year 11 lessons that include practice with exam-style questions or assessment preparation.

**Query:**
```cypher
// Find assessment-focused lessons
MATCH (year:Year {yearTitle: "11"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
WHERE lesson.lessonTitle CONTAINS 'exam' 
   OR lesson.lessonTitle CONTAINS 'assessment'
   OR lesson.lessonTitle CONTAINS 'extended response'
   OR any(outline IN lesson.lessonOutline WHERE outline CONTAINS 'exam')
RETURN lesson.lessonTitle AS lesson,
       lesson.pupilLessonOutcome AS outcome,
       lesson.lessonOutline AS structure
ORDER BY lesson.lessonTitle
LIMIT 10;
```

**Results:**
| lesson | outcome | structure |
|--------|---------|-----------|
| Analysing extended responses to the Eduqas poetry anthology | I can recognise excellent writing practice in a model response. | ["{\"lesson_outline\": \"Exploring model introductions\"}", "{\"lesson_outline\": \"Exploring model comparative analysis\"}"] |

**Interpretation:**
This lesson explicitly teaches exam technique through model answers. It should be scheduled in the revision period with adequate time for practice.

**Query Variations:**
- Search for specific assessment types: "essay", "comparative", "analytical"
- Add `misconceptionsMistakes` to identify common exam errors
- Filter by exam board to ensure alignment with assessment objectives

---

### Use Case 9: Supporting New Teachers

**Scenario:** A newly qualified teacher needs resources for teaching a unit. They want to see all teacher tips and misconceptions for a specific unit.

**Query:**
```cypher
// Get comprehensive teaching guidance for a unit
MATCH (unit:Unit {unitSlug: "poetry-anthology-first-study"})-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
WHERE lesson.teacherTips IS NOT NULL OR lesson.misconceptionsMistakes IS NOT NULL
RETURN lesson.lessonTitle AS lesson,
       lesson.teacherTips AS tips,
       lesson.misconceptionsMistakes AS misconceptions,
       lesson.equipmentResources AS resources
ORDER BY lesson.lessonTitle
LIMIT 5;
```

**Results:**
| lesson | tips | misconceptions | resources |
|--------|------|----------------|-----------|
| Analysing extended responses to the Eduqas poetry anthology | ["{\"teacher_tip\": \"If pupils have already written their own paragraphs or essays, Task A and Task B can be adapted to help them review and improve their own work.\"}"] | ["{\"response\": \"Without analysis, the response does not explain how or why the poets present their ideas...\", \"misconception\": \"As long as I include quotations from both poems and mention some similarities or differences, I'm doing a good comparative analysis.\"}"] | ["{\"equipment\": \"You will need a copy of the Eduqas 2025 Anthology for this lesson.\"}"] |

**Interpretation:**
The teacher tips provide practical classroom strategies, misconceptions highlight common student errors to address, and resources list essential materials.

**Query Variations:**
- Filter by `WHERE lesson.misconceptionsMistakes IS NOT NULL` to focus on challenging concepts
- Add `lesson.keyLearningPoints` to see core content
- Group by unit to get comprehensive unit-level guidance

---

### Use Case 10: Keyword-Based Resource Discovery

**Scenario:** A teacher planning a scheme of work on Romanticism wants to find all relevant lessons across the curriculum.

**Query:**
```cypher
// Find lessons by keyword theme
MATCH (lesson:Lesson)
WHERE any(keyword IN lesson.keywords WHERE keyword CONTAINS 'Romantic')
WITH lesson
MATCH (lesson)<-[:HAS_LESSON]-(:Unitvariant)<-[:HAS_UNITVARIANT]-(unit:Unit)<-[:HAS_UNIT]-(:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject)
RETURN DISTINCT lesson.lessonTitle AS lesson,
       subject.subjectTitle AS subject,
       unit.unitTitle AS unit,
       [kw IN lesson.keywords WHERE kw CONTAINS 'Romantic'][0] AS romanticKeyword
ORDER BY subject.subjectTitle, lesson.lessonTitle
LIMIT 10;
```

**Results:**
| lesson | subject | unit | romanticKeyword |
|--------|---------|------|-----------------|
| Understanding the tone of Brontë's 'Mild the Mist Upon the Hill' | English | Belonging: poetry | {"keyword": "Romanticism", "description": "an artistic movement from the late 18th and early 19th century, focused on emotions and nature"} |

**Interpretation:**
This lesson explicitly teaches Romanticism as a literary movement. The keyword description provides definitional support for teaching.

**Query Variations:**
- Search for other literary movements: "Victorian", "Modernist"
- Search for techniques: "metaphor", "personification", "imagery"
- Cross-reference with year groups to ensure age-appropriate content

---

### Use Case 11: Analyzing Pedagogical Scaffolding

**Scenario:** A school's teaching and learning team wants to identify exemplar lessons with rich pedagogical scaffolding for CPD purposes.

**Query:**
```cypher
// Find lessons with comprehensive pedagogical support
MATCH (lesson:Lesson)
WHERE lesson.keywords IS NOT NULL 
  AND lesson.keyLearningPoints IS NOT NULL
  AND lesson.misconceptionsMistakes IS NOT NULL
  AND lesson.teacherTips IS NOT NULL
WITH lesson,
     size(lesson.keywords) AS keywords,
     size(lesson.keyLearningPoints) AS learningPoints,
     size(lesson.misconceptionsMistakes) AS misconceptions,
     size(lesson.teacherTips) AS tips
WHERE keywords >= 4 AND learningPoints >= 4 AND misconceptions >= 1 AND tips >= 1
RETURN lesson.lessonTitle AS lesson,
       lesson.pupilLessonOutcome AS outcome,
       keywords, learningPoints, misconceptions, tips,
       keywords + learningPoints + misconceptions + tips AS totalScaffold
ORDER BY totalScaffold DESC
LIMIT 10;
```

**Results:**
| lesson | outcome | keywords | learningPoints | misconceptions | tips | totalScaffold |
|--------|---------|----------|----------------|----------------|------|---------------|
| Analysing how poets present relationships that change over time | I can write a comparative analysis of 'Walking Away' and one other poem. | 5 | 4 | 1 | 1 | 11 |

**Interpretation:**
These lessons demonstrate best practice in pedagogical design with multiple forms of support. They can serve as templates for other lessons.

**Query Variations:**
- Add subject or year filters to find exemplars in specific contexts
- Compare scaffolding levels across exam boards
- Identify lessons with minimal scaffolding that need development

---

### Use Case 12: Unit Sequencing Based on Threads

**Scenario:** A head of department wants to sequence units so that students experience thematic coherence through learning threads.

**Query:**
```cypher
// Map units to threads for sequencing decisions
MATCH (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(:Unitoffering)-[:HAS_UNIT]->(unit:Unit),
      (unit)-[:HAS_THREAD]->(thread:Thread)
WITH unit, collect(thread.threadTitle) AS threads, count(thread) AS threadCount
RETURN unit.unitTitle AS unit,
       threads,
       threadCount,
       unit.whyThisWhyNow AS rationale
ORDER BY threadCount DESC, unit.unitTitle
LIMIT 10;
```

**Results:**
| unit | threads | threadCount | rationale |
|------|---------|-------------|-----------|
| Poetry anthology: first study | ["Appreciation of poetry", "Modern literature strand 1: identity, belonging and community", "Modern literature strand 2: power, control and oppressive regimes"] | 3 | This unit uses and builds on pupils' understanding of comparative poetry analysis from 'Comparing poetry from the first world war'... |

**Interpretation:**
This unit connects to three major threads, making it ideal for mid-year placement where it can draw on and feed into other units.

**Query Variations:**
- Filter to units with specific thread combinations
- Add year group context to plan vertical progression
- Include lesson counts to estimate time allocation
- Cross-reference with exam board variants for qualification-specific sequencing

---

## 8. Advanced Queries

### 8.1 Multi-hop Traversals

#### Finding Learning Pathways Through Prerequisite Chains

```cypher
// Find all units that build on a specific topic
MATCH path = (start:Unit {unitSlug: "states-of-matter"})-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson),
             (later:Unit)
WHERE start <> later
  AND any(prereq IN later.priorKnowledge WHERE prereq CONTAINS 'particle')
RETURN DISTINCT later.unitTitle AS nextUnit,
       later.priorKnowledge AS prerequisites,
       length(path) AS pathLength
LIMIT 10;
```

**Purpose:** Discover learning sequences and curriculum dependencies.

---

#### Traversing from Phase to Lesson in One Query

```cypher
// Complete educational hierarchy traversal
MATCH path = (phase:Phase {phaseSlug: "secondary"})-[:HAS_KEY_STAGE*1..2]->(:Keystage)-[:HAS_YEAR]->(:Year)-[:HAS_UNIT_OFFERING]->(:Unitoffering)-[:HAS_UNIT]->(:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
RETURN phase.phaseTitle AS phase,
       nodes(path)[2].keyStageTitle AS keyStage,
       nodes(path)[3].yearTitle AS year,
       nodes(path)[6].unitTitle AS unit,
       lesson.lessonTitle AS lesson
LIMIT 5;
```

**Purpose:** Navigate the full hierarchy efficiently with variable-length path matching.

---

### 8.2 Pattern Matching

#### Finding Units That Appear Across Multiple Year Groups

```cypher
// Identify reusable units
MATCH (unit:Unit)<-[:HAS_UNIT]-(:Unitoffering)<-[:HAS_UNIT_OFFERING]-(year:Year)
WITH unit, collect(DISTINCT year.yearTitle) AS years
WHERE size(years) > 1
RETURN unit.unitTitle AS unit,
       years,
       size(years) AS yearCount
ORDER BY yearCount DESC, unit.unitTitle
LIMIT 10;
```

**Purpose:** Find units designed for multiple year groups, indicating curriculum flexibility.

---

#### Optional Pattern Matching for Incomplete Data

```cypher
// Find lessons with or without teacher tips
MATCH (lesson:Lesson)
OPTIONAL MATCH (lesson)<-[:HAS_LESSON]-(uv:Unitvariant)<-[:HAS_UNITVARIANT]-(unit:Unit)
RETURN lesson.lessonTitle AS lesson,
       unit.unitTitle AS unit,
       CASE WHEN lesson.teacherTips IS NOT NULL THEN 'Yes' ELSE 'No' END AS hasTips,
       size(coalesce(lesson.teacherTips, [])) AS tipCount
ORDER BY tipCount DESC
LIMIT 10;
```

**Purpose:** Gracefully handle optional relationships and properties.

---

### 8.3 Aggregations and Analytics

#### Curriculum Complexity Heatmap

```cypher
// Analyze curriculum complexity by subject and year
MATCH (year:Year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject),
      (uo)-[:HAS_UNIT]->(unit:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
WITH year, subject, 
     count(DISTINCT unit) AS units,
     count(DISTINCT lesson) AS lessons,
     avg(size(lesson.keyLearningPoints)) AS avgLearningPoints
RETURN year.yearTitle AS year,
       subject.subjectTitle AS subject,
       units,
       lessons,
       round(avgLearningPoints * 100) / 100 AS avgLearningPoints
ORDER BY year.yearId, lessons DESC;
```

**Purpose:** Create a comprehensive view of curriculum density.

---

#### Statistical Analysis of Pedagogical Support

```cypher
// Analyze distribution of pedagogical features
MATCH (lesson:Lesson)
RETURN 
  count(lesson) AS totalLessons,
  count(lesson.keywords) AS lessonsWithKeywords,
  count(lesson.misconceptionsMistakes) AS lessonsWithMisconceptions,
  count(lesson.teacherTips) AS lessonsWithTips,
  round(100.0 * count(lesson.keywords) / count(lesson)) AS percentWithKeywords,
  round(100.0 * count(lesson.misconceptionsMistakes) / count(lesson)) AS percentWithMisconceptions,
  round(100.0 * count(lesson.teacherTips) / count(lesson)) AS percentWithTips;
```

**Purpose:** Measure pedagogical quality across the curriculum.

---

### 8.4 Graph Algorithms

#### Shortest Path Between Subjects via Threads

```cypher
// Find thematic connections between subjects
MATCH path = shortestPath(
  (s1:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING*]->(:Unitoffering)-[:HAS_UNIT*]->(:Unit)-[:HAS_THREAD*]->(:Thread)-[:HAS_THREAD*]->(:Unit)<-[:HAS_UNIT*]-(:Unitoffering)<-[:HAS_UNIT_OFFERING*]-(s2:Subject {subjectSlug: "history"})
)
WHERE s1 <> s2
RETURN [node IN nodes(path) WHERE 'Thread' IN labels(node) | node.threadTitle] AS connectingThreads,
       length(path) AS pathLength
LIMIT 5;
```

**Purpose:** Discover cross-curricular connections through shared themes.

---

#### Node Degree Centrality (Most Connected Units)

```cypher
// Find units with the most connections
MATCH (unit:Unit)
WITH unit,
     count{(unit)-[:HAS_THREAD]->(:Thread)} AS threadConnections,
     count{(unit)-[:HAS_UNITVARIANT]->(:Unitvariant)} AS variants,
     count{(:Unitoffering)-[:HAS_UNIT]->(unit)} AS offerings
WITH unit, threadConnections + variants + offerings AS totalConnections
RETURN unit.unitTitle AS unit,
       threadConnections,
       variants,
       offerings,
       totalConnections
ORDER BY totalConnections DESC
LIMIT 10;
```

**Purpose:** Identify central curriculum units that connect many elements.

---

#### Similarity Analysis Using Jaccard Index

```cypher
// Find units with similar keyword profiles
MATCH (u1:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(l1:Lesson),
      (u2:Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(l2:Lesson)
WHERE u1.unitSlug < u2.unitSlug
  AND l1.keywords IS NOT NULL
  AND l2.keywords IS NOT NULL
WITH u1, u2, 
     collect(DISTINCT l1.keywords) AS keywords1,
     collect(DISTINCT l2.keywords) AS keywords2
WITH u1, u2,
     size([k IN keywords1 WHERE k IN keywords2]) AS intersection,
     size(keywords1 + keywords2) AS union
WHERE intersection > 0
RETURN u1.unitTitle AS unit1,
       u2.unitTitle AS unit2,
       round(100.0 * intersection / union) AS similarityPercent
ORDER BY similarityPercent DESC
LIMIT 10;
```

**Purpose:** Find units with overlapping pedagogical content.

---

## 9. Query Optimization Tips

### Indexing Recommendations

**Create Indexes on Frequently Queried Properties:**

```cypher
// Essential indexes for performance
CREATE INDEX subject_slug IF NOT EXISTS FOR (s:Subject) ON (s.subjectSlug);
CREATE INDEX year_title IF NOT EXISTS FOR (y:Year) ON (y.yearTitle);
CREATE INDEX unit_slug IF NOT EXISTS FOR (u:Unit) ON (u.unitSlug);
CREATE INDEX lesson_slug IF NOT EXISTS FOR (l:Lesson) ON (l.lessonSlug);
CREATE INDEX examboard_slug IF NOT EXISTS FOR (e:Examboard) ON (e.examBoardSlug);
CREATE INDEX keystage_slug IF NOT EXISTS FOR (k:Keystage) ON (k.keyStageSlug);
```

**Composite Indexes for Complex Queries:**

```cypher
// For year + subject queries
CREATE INDEX unit_offering_slug IF NOT EXISTS FOR (uo:Unitoffering) ON (uo.unitOfferingSlug);
```

---

### Query Performance Best Practices

**💡 Tip 1: Start with the Most Selective Node**

```cypher
// Good: Start with specific lesson (12,631 lessons total)
MATCH (lesson:Lesson {lessonSlug: "specific-lesson"})<-[:HAS_LESSON]-(uv:Unitvariant)
RETURN lesson, uv;

// Bad: Start with all unitvariants (2,064 nodes)
MATCH (uv:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson {lessonSlug: "specific-lesson"})
RETURN lesson, uv;
```

---

**💡 Tip 2: Use Parameters for Better Plan Caching**

```cypher
// Good: Parameterized query (reuses execution plan)
MATCH (year:Year {yearTitle: $yearTitle})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)
RETURN uo;

// Less efficient: Hardcoded values (new plan each time)
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)
RETURN uo;
```

---

**💡 Tip 3: Limit Early When Possible**

```cypher
// Good: Limit before expensive operations
MATCH (lesson:Lesson)
WITH lesson LIMIT 100
MATCH (lesson)<-[:HAS_LESSON]-(uv:Unitvariant)<-[:HAS_UNITVARIANT]-(unit:Unit)
RETURN lesson, unit;

// Bad: Limit after all traversals
MATCH (lesson:Lesson)<-[:HAS_LESSON]-(uv:Unitvariant)<-[:HAS_UNITVARIANT]-(unit:Unit)
RETURN lesson, unit
LIMIT 100;
```

---

**💡 Tip 4: Use DISTINCT Judiciously**

```cypher
// Only use DISTINCT when necessary
MATCH (year:Year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)-[:HAS_UNIT]->(unit:Unit)
WHERE year.yearTitle = "10"
RETURN DISTINCT unit.unitTitle;  // Necessary due to multiple offerings

// Avoid unnecessary DISTINCT
MATCH (subject:Subject)
RETURN subject.subjectTitle;  // Already unique, no DISTINCT needed
```

---

**💡 Tip 5: Profile Your Queries**

```cypher
// Use PROFILE to analyze query execution
PROFILE
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)-[:HAS_UNIT]->(unit:Unit)
RETURN count(unit);
```

**Look for:**
- `db hits`: Lower is better
- `rows`: Minimize intermediate row counts
- `NodeByLabelScan` vs `NodeIndexSeek`: Index seek is faster

---

### Common Pitfalls to Avoid

**⚠️ Pitfall 1: Cartesian Products**

```cypher
// Bad: Creates cartesian product
MATCH (year:Year), (subject:Subject)
RETURN year, subject;  // Returns 11 × 22 = 242 rows

// Good: Use proper relationships
MATCH (year:Year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject)
RETURN year, subject;
```

---

**⚠️ Pitfall 2: Unbounded Variable-Length Paths**

```cypher
// Dangerous: No upper limit on path length
MATCH path = (:Unit)-[:HAS_THREAD*]->(:Thread)
RETURN path;

// Safe: Bounded path length
MATCH path = (:Unit)-[:HAS_THREAD*1..3]->(:Thread)
RETURN path;
```

---

**⚠️ Pitfall 3: Large IN Clauses**

```cypher
// Inefficient: Large IN list
WHERE lesson.lessonId IN [1,2,3,4,5,...,1000]

// Better: Use UNWIND with parameters
UNWIND $lessonIds AS lessonId
MATCH (lesson:Lesson {lessonId: lessonId})
RETURN lesson;
```

---

## 10. Data Quality Notes

### Known Limitations

**1. Data Completeness**
- Some lessons may lack `teacherTips` or `misconceptionsMistakes` (this is by design - not all lessons need these)
- `priorKnowledge` is optional and present on ~60% of units
- `contentGuidance` is only present for lessons with sensitive content

**2. Data Consistency**
- JSON-formatted properties (keywords, keyLearningPoints) require parsing in application code
- Property names follow camelCase convention from the source system
- List properties stored as Neo4j arrays with JSON string elements

**3. Temporal Data**
- `lastUpdated` timestamps indicate when data was imported, not when content was created
- No historical versioning - current state only
- Schema version tracked in Schemaversion node

---

### Update Frequency

**Current State:**
- **Schema Version:** v0.1.0-alpha (experimental/design phase)
- **Last Updated:** October 8, 2025
- **Data Refresh:** Manual updates from Hasura source system

**Future Updates:**
- Planned transition to automated synchronization
- Will add `effectiveDate` and `retiredDate` for temporal tracking
- Versioned schemas for backward compatibility

---

### Data Sources and Methodology

**Source Systems:**
- **Primary:** Oak National Academy Hasura GraphQL API
- **Materialized Views:** Published curriculum data (18,238+ records)
- **Extract Method:** GraphQL queries with composite key joins
- **Transform:** CSV-based mapping with deduplication

**Data Pipeline:**
1. Extract from Hasura materialized views
2. Clean and normalize data (Unicode, empty values, quotes)
3. Map to Neo4j schema with type conversion
4. Bulk import via UNWIND batch queries (1,000 records/batch)

**Quality Assurance:**
- 100% test coverage on pipeline components
- Integration tests with realistic curriculum data
- Manual validation of complex relationships (threads, variants)

---

### Version Information

**Schema Evolution:**
- **v0.1.0-alpha:** Initial graph design with 13 node types, 8 relationship types
- Added support for:
  - Composite key joins (programme_slug_by_year)
  - Array field expansion (threads)
  - Computed properties (isOptional)
  - Native list types for complex objects

**Breaking Changes:**
- None (alpha version)

**Deprecations:**
- None (alpha version)

---

### Data Dictionary Notes

**Special Property Formats:**

**JSON String Lists** (keywords, keyLearningPoints, etc.):
```json
[
  "{\"keyword\": \"nostalgia\", \"description\": \"a feeling of pleasure...\"}",
  "{\"keyword\": \"melancholic\", \"description\": \"expressing feelings of sadness\"}"
]
```
Parse each array element as JSON to access structured data.

**Content Guidance Codes:**
- "2": Violence
- "4": Grief/Loss
- "9": Discrimination
- "10": Other sensitive themes
- "14": Historical trauma

**Display Order:**
- Lower values appear first in UI
- Used for sorting: Subjects, Years, Key Stages

---

## 11. Appendices

### Appendix A: Complete Cypher Reference

**Basic Navigation Queries:**
```cypher
// 1. List all subjects
MATCH (s:Subject) RETURN s.subjectTitle ORDER BY s.displayOrder;

// 2. Find units for a subject
MATCH (s:Subject {subjectSlug: $slug})-[:HAS_UNIT_OFFERING]->()-[:HAS_UNIT]->(u:Unit)
RETURN DISTINCT u.unitTitle;

// 3. Get lessons in a unit
MATCH (u:Unit {unitSlug: $slug})-[:HAS_UNITVARIANT]->()-[:HAS_LESSON]->(l:Lesson)
RETURN l.lessonTitle, l.pupilLessonOutcome;

// 4. Find year groups in a key stage
MATCH (ks:Keystage {keyStageSlug: $slug})-[:HAS_YEAR]->(y:Year)
RETURN y.yearTitle ORDER BY y.displayOrder;
```

**Analysis Queries:**
```cypher
// 5. Curriculum coverage by subject
MATCH (s:Subject)-[:HAS_UNIT_OFFERING]->()-[:HAS_UNIT]->(u:Unit)-[:HAS_UNITVARIANT]->()-[:HAS_LESSON]->(l:Lesson)
RETURN s.subjectTitle, count(DISTINCT u) AS units, count(l) AS lessons
ORDER BY lessons DESC;

// 6. Units by thread
MATCH (t:Thread)<-[:HAS_THREAD]-(u:Unit)
RETURN t.threadTitle, collect(u.unitTitle) AS units;

// 7. Exam board comparison
MATCH (eb:Examboard)-[:HAS_PROGRAMME]->()-[:HAS_UNITVARIANT]->(uv:Unitvariant)
WITH eb, count(uv) AS variants
RETURN eb.examBoardTitle, variants ORDER BY variants DESC;

// 8. Lesson complexity
MATCH (l:Lesson)
RETURN l.lessonTitle, 
       size(l.keywords) + size(l.keyLearningPoints) AS complexity
ORDER BY complexity DESC LIMIT 10;
```

**Admin Queries:**
```cypher
// 9. Database statistics
MATCH (n) RETURN labels(n)[0] AS type, count(n) AS count ORDER BY count DESC;

// 10. Relationship statistics
MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC;
```

---

### Appendix B: Property Reference

**Complete Node Property Listing:**

**Phase Properties:**
- `phaseId` (INTEGER): Unique identifier
- `phaseSlug` (STRING): URL-friendly key
- `phaseTitle` (STRING): Display name
- `phaseDescription` (STRING): Full description
- `displayOrder` (INTEGER): Sort order
- `lastUpdated` (STRING): ISO timestamp

**Keystage Properties:**
- `keyStageId` (INTEGER): Unique identifier
- `keyStageSlug` (STRING): URL-friendly key ("ks1", "ks2", etc.)
- `keyStageTitle` (STRING): Display name ("KS1", "KS2", etc.)
- `keyStageDescription` (STRING): Full description
- `displayOrder` (INTEGER): Sort order
- `lastUpdated` (STRING): ISO timestamp

**Year Properties:**
- `yearId` (INTEGER): Unique identifier (1-11)
- `yearSlug` (STRING): URL-friendly key ("year-1" to "year-11")
- `yearTitle` (STRING): Display name ("1" to "11")
- `yearDescription` (STRING): Full description ("Year 1" to "Year 11")
- `displayOrder` (INTEGER): Sort order
- `lastUpdated` (STRING): ISO timestamp

**Subject Properties:**
- `subjectId` (INTEGER): Unique identifier
- `subjectSlug` (STRING): URL-friendly key
- `subjectTitle` (STRING): Display name
- `subjectDescription` (STRING, optional): Key stage range
- `subjectParentId` (INTEGER, optional): Parent subject ID
- `subjectParentTitle` (STRING, optional): Parent subject name
- `displayOrder` (INTEGER): Sort order
- `lastUpdated` (STRING): ISO timestamp

**Unitoffering Properties:**
- `unitOfferingSlug` (STRING): Composite identifier (e.g., "year-10-english")
- `lastUpdated` (STRING): ISO timestamp

**Unit Properties:**
- `unitId` (INTEGER): Unique identifier
- `unitSlug` (STRING): URL-friendly key
- `unitTitle` (STRING): Display name
- `unitDescription` (STRING): Full description of unit content
- `whyThisWhyNow` (STRING, optional): Pedagogical rationale
- `priorKnowledge` (LIST OF STRING, optional): Required prerequisite skills
- `subjectCategory` (LIST OF STRING, optional): Subject area tags
- `nullUnitVariantId` (INTEGER): Default variant ID
- `lastUpdated` (STRING): ISO timestamp

**Unitvariant Properties:**
- `unitVariantId` (INTEGER): Unique identifier
- `optionTitle` (STRING): Exam board variant name
- `lastUpdated` (STRING): ISO timestamp

**Lesson Properties:**
- `lessonId` (INTEGER): Unique identifier
- `lessonSlug` (STRING): URL-friendly key
- `lessonTitle` (STRING): Display name
- `pupilLessonOutcome` (STRING): Learning objective
- `keywords` (LIST OF STRING): Key terms as JSON objects
- `keyLearningPoints` (LIST OF STRING): Core concepts as JSON objects
- `lessonOutline` (LIST OF STRING): Lesson structure as JSON objects
- `misconceptionsMistakes` (LIST OF STRING, optional): Common errors as JSON objects
- `equipmentResources` (LIST OF STRING, optional): Required materials as JSON objects
- `teacherTips` (LIST OF STRING, optional): Teaching guidance as JSON objects
- `contentGuidance` (LIST OF STRING, optional): Content warning codes
- `contentGuidanceDetails` (LIST OF STRING, optional): Content warning descriptions
- `quizStarterId` (INTEGER): Starter quiz ID
- `quizExitId` (INTEGER): Exit quiz ID
- `lastUpdated` (STRING): ISO timestamp

**Thread Properties:**
- `threadId` (INTEGER): Unique identifier
- `thread_slug` (STRING): URL-friendly key
- `threadTitle` (STRING): Thematic strand name
- `lastUpdated` (STRING): ISO timestamp

**Examboard Properties:**
- `examBoardId` (INTEGER): Unique identifier
- `examBoardSlug` (STRING): URL-friendly key
- `examBoardTitle` (STRING): Display abbreviation
- `examBoardDescription` (STRING): Full name
- `displayOrder` (INTEGER): Sort order
- `lastUpdated` (STRING): ISO timestamp

**Tier Properties:**
- `tierId` (INTEGER): Unique identifier
- `tierSlug` (STRING): URL-friendly key
- `tierTitle` (STRING): Display name
- `tierDescription` (STRING): Full description
- `displayOrder` (INTEGER): Sort order
- `lastUpdated` (STRING): ISO timestamp

**Programme Properties:**
- `programmeSlug` (STRING): Composite identifier (subject-phase-year-examboard)
- `lastUpdated` (STRING): ISO timestamp

**Schemaversion Properties:**
- `schemaVersion` (STRING): Version identifier
- `schemaDescription` (STRING): Version notes
- `isActive` (BOOLEAN): Active status
- `lastUpdated` (STRING): ISO timestamp

---

### Appendix C: Glossary

**UK Curriculum Terms:**

**EYFS (Early Years Foundation Stage):** Ages 3-5, pre-primary education

**Key Stage (KS):** Organizational division of the UK curriculum
- **KS1:** Years 1-2 (ages 5-7)
- **KS2:** Years 3-6 (ages 7-11)
- **KS3:** Years 7-9 (ages 11-14)
- **KS4:** Years 10-11 (ages 14-16, GCSE years)

**GCSE (General Certificate of Secondary Education):** Qualification taken at age 16 (end of Year 11)

**Tier:** GCSE difficulty level
- **Foundation:** Covers grades 1-5
- **Higher:** Covers grades 4-9

**Exam Boards:** Organizations that provide GCSE qualifications
- **AQA:** Assessment and Qualifications Alliance
- **Edexcel:** Pearson Edexcel
- **Eduqas:** Welsh exam board
- **OCR:** Oxford, Cambridge and RSA
- **WJEC:** Welsh Joint Education Committee

---

**Graph Database Terms:**

**Node:** An entity in the graph (Subject, Unit, Lesson, etc.)

**Relationship:** A connection between nodes (HAS_UNIT, HAS_LESSON, etc.)

**Label:** A node type identifier (`:Lesson`, `:Unit`, `:Subject`)

**Property:** A key-value attribute on a node or relationship

**Cypher:** Neo4j's query language (similar to SQL for graphs)

**Traversal:** Following relationships to navigate the graph

**Path:** A sequence of nodes and relationships

**Pattern Matching:** Finding specific graph structures using MATCH

---

**Pedagogical Terms:**

**Learning Objective:** What students will be able to do by the end of a lesson (`pupilLessonOutcome`)

**Key Learning Points:** Core concepts students must understand

**Misconceptions:** Common student errors or misunderstandings

**Prior Knowledge:** Skills/knowledge students need before starting a unit

**Differentiation:** Adapting content for different ability levels (Foundation vs Higher)

**Thread:** Thematic strand connecting related units across year groups

**Unit:** Collection of related lessons on a topic (typically 6-15 lessons)

**Starter Quiz:** Pre-lesson assessment to activate prior knowledge

**Exit Quiz:** Post-lesson assessment to check understanding

---

**Technical Terms:**

**Materialized View (MV):** Pre-computed database view for performance

**Slug:** URL-friendly identifier (lowercase, hyphen-separated)

**Junction Node:** Node connecting two other node types (Unitoffering)

**Variant:** Exam board-specific version of a unit

**Composite Key:** Multiple fields used together for uniqueness

**UNWIND:** Cypher command to expand lists into rows

**Cardinality:** Number of items (nodes, relationships, properties)

---

## Conclusion

This UK School Curriculum Knowledge Graph provides a powerful foundation for curriculum planning, pedagogical analysis, and educational research. The graph's hierarchical structure combined with cross-cutting thematic threads enables both detailed lesson-level queries and high-level curriculum analytics.

**Key Strengths:**
- **Comprehensive Coverage:** 12,631 lessons across 22 subjects
- **Rich Metadata:** Keywords, learning points, misconceptions, and teaching tips
- **Flexible Organization:** Multiple pathways through educational structure, content hierarchy, and qualification routes
- **Cross-Curricular Connections:** Thread relationships enable thematic curriculum planning
- **Exam Board Support:** Full coverage of AQA, Edexcel, Eduqas, OCR, and WJEC specifications

**Getting Help:**
- Neo4j Community: https://community.neo4j.com
- Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- Oak National Academy: https://www.thenational.academy

**Next Steps:**
1. Try the basic queries in Section 5.2 to familiarize yourself with the data
2. Explore the practical use cases in Section 7 for your specific needs
3. Use the Cypher reference in Appendix A as a quick lookup
4. Experiment with advanced patterns in Section 8 for deeper insights

---

**Document Version:** 1.0
**Last Updated:** October 2025
**Total Lines:** 3,100+
**Total Queries:** 50+

*This documentation was generated for the Oak National Academy UK Curriculum Knowledge Graph (Schema v0.1.0-alpha)*


---

## Additional Resources

### Sample Query Templates

Below are copy-paste templates for common scenarios. Replace `$parameter` with your actual values.

**Template 1: Find All Content for a Specific Context**
```cypher
// Find lessons for Year $year, Subject $subject, Exam Board $examBoard
MATCH (year:Year {yearTitle: $year})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: $subject})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(unit:Unit)-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (eb:Examboard {examBoardSlug: $examBoard})-[:HAS_PROGRAMME]->(prog:Programme),
      (prog)-[:HAS_UNITVARIANT]->(uv),
      (uv)-[:HAS_LESSON]->(lesson:Lesson)
RETURN unit.unitTitle AS unit,
       lesson.lessonTitle AS lesson,
       lesson.pupilLessonOutcome AS outcome
ORDER BY unit.unitTitle, lesson.lessonTitle;
```

**Template 2: Search Lessons by Content**
```cypher
// Search for lessons containing $searchTerm in keywords or learning points
MATCH (lesson:Lesson)
WHERE any(keyword IN lesson.keywords WHERE keyword CONTAINS $searchTerm)
   OR any(point IN lesson.keyLearningPoints WHERE point CONTAINS $searchTerm)
   OR lesson.lessonTitle CONTAINS $searchTerm
RETURN lesson.lessonTitle AS lesson,
       lesson.pupilLessonOutcome AS outcome,
       lesson.keywords[0..3] AS sampleKeywords
LIMIT 20;
```

**Template 3: Export Unit Structure for Planning**
```cypher
// Export complete unit structure for $unitSlug
MATCH (unit:Unit {unitSlug: $unitSlug})
OPTIONAL MATCH (unit)-[:HAS_THREAD]->(thread:Thread)
OPTIONAL MATCH (unit)-[:HAS_UNITVARIANT]->(uv:Unitvariant)-[:HAS_LESSON]->(lesson:Lesson)
RETURN unit.unitTitle AS unit,
       unit.unitDescription AS description,
       unit.whyThisWhyNow AS rationale,
       unit.priorKnowledge AS prerequisites,
       collect(DISTINCT thread.threadTitle) AS threads,
       collect(DISTINCT {
         lesson: lesson.lessonTitle,
         outcome: lesson.pupilLessonOutcome,
         keywords: size(lesson.keywords),
         learningPoints: size(lesson.keyLearningPoints)
       }) AS lessons;
```

**Template 4: Compare Exam Boards**
```cypher
// Compare all exam boards for $unitSlug
MATCH (unit:Unit {unitSlug: $unitSlug})-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (prog:Programme)-[:HAS_UNITVARIANT]->(uv),
      (eb:Examboard)-[:HAS_PROGRAMME]->(prog)
OPTIONAL MATCH (uv)-[:HAS_LESSON]->(lesson:Lesson)
RETURN eb.examBoardTitle AS examBoard,
       uv.optionTitle AS variant,
       count(lesson) AS lessonCount,
       collect(DISTINCT lesson.lessonTitle)[0..5] AS sampleLessons
ORDER BY examBoard;
```

**Template 5: Find Cross-Curricular Links**
```cypher
// Find subjects that share thematic thread $threadTitle
MATCH (thread:Thread {threadTitle: $threadTitle})-[:HAS_THREAD]-(unit:Unit),
      (unit)<-[:HAS_UNIT]-(uo:Unitoffering)<-[:HAS_UNIT_OFFERING]-(subject:Subject)
WITH subject, collect(DISTINCT unit.unitTitle) AS units
RETURN subject.subjectTitle AS subject,
       units,
       size(units) AS unitCount
ORDER BY unitCount DESC;
```

---

### Integration Examples

#### Python Integration with neo4j Driver

```python
from neo4j import GraphDatabase
import json

class CurriculumGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def get_year_curriculum(self, year, subject):
        """Get all units for a year/subject combination"""
        query = """
        MATCH (year:Year {yearTitle: $year})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
              (subject:Subject {subjectSlug: $subject})-[:HAS_UNIT_OFFERING]->(uo),
              (uo)-[:HAS_UNIT]->(unit:Unit)
        RETURN DISTINCT unit.unitTitle AS unit,
               unit.unitDescription AS description,
               unit.whyThisWhyNow AS rationale
        ORDER BY unit.unitTitle
        """
        with self.driver.session() as session:
            result = session.run(query, year=year, subject=subject)
            return [record.data() for record in result]
    
    def search_lessons_by_keyword(self, keyword):
        """Search for lessons containing a specific keyword"""
        query = """
        MATCH (lesson:Lesson)
        WHERE any(kw IN lesson.keywords WHERE kw CONTAINS $keyword)
        RETURN lesson.lessonTitle AS title,
               lesson.pupilLessonOutcome AS outcome,
               lesson.keywords AS keywords
        LIMIT 10
        """
        with self.driver.session() as session:
            result = session.run(query, keyword=keyword)
            lessons = []
            for record in result:
                lesson = record.data()
                # Parse JSON keywords
                lesson['keywords'] = [json.loads(k) for k in lesson['keywords']]
                lessons.append(lesson)
            return lessons
    
    def get_unit_prerequisites(self, unit_slug):
        """Get prerequisite knowledge for a unit"""
        query = """
        MATCH (unit:Unit {unitSlug: $slug})
        RETURN unit.unitTitle AS unit,
               unit.priorKnowledge AS prerequisites
        """
        with self.driver.session() as session:
            result = session.run(query, slug=unit_slug)
            return result.single().data()

# Usage example
graph = CurriculumGraph("bolt://localhost:7687", "neo4j", "password")

# Get Year 10 English curriculum
curriculum = graph.get_year_curriculum("10", "english")
for unit in curriculum:
    print(f"Unit: {unit['unit']}")
    print(f"Description: {unit['description'][:100]}...")
    print()

# Search for Romanticism lessons
lessons = graph.search_lessons_by_keyword("Romantic")
for lesson in lessons:
    print(f"Lesson: {lesson['title']}")
    for kw in lesson['keywords']:
        if 'Romantic' in kw.get('keyword', ''):
            print(f"  Keyword: {kw['keyword']} - {kw['description']}")
    print()

graph.close()
```

---

#### JavaScript Integration with neo4j-driver

```javascript
const neo4j = require('neo4j-driver');

class CurriculumGraph {
    constructor(uri, user, password) {
        this.driver = neo4j.driver(uri, neo4j.auth.basic(user, password));
    }

    async close() {
        await this.driver.close();
    }

    async getLessonDetails(lessonSlug) {
        const session = this.driver.session();
        try {
            const result = await session.run(`
                MATCH (lesson:Lesson {lessonSlug: $slug})
                OPTIONAL MATCH (lesson)<-[:HAS_LESSON]-(uv:Unitvariant)<-[:HAS_UNITVARIANT]-(unit:Unit)
                RETURN lesson, unit.unitTitle AS unit
            `, { slug: lessonSlug });

            if (result.records.length === 0) return null;

            const record = result.records[0];
            const lesson = record.get('lesson').properties;
            
            // Parse JSON arrays
            lesson.keywords = lesson.keywords?.map(k => JSON.parse(k)) || [];
            lesson.keyLearningPoints = lesson.keyLearningPoints?.map(k => JSON.parse(k)) || [];
            
            return {
                ...lesson,
                unit: record.get('unit')
            };
        } finally {
            await session.close();
        }
    }

    async getExamBoardComparison(unitSlug) {
        const session = this.driver.session();
        try {
            const result = await session.run(`
                MATCH (unit:Unit {unitSlug: $slug})-[:HAS_UNITVARIANT]->(uv:Unitvariant),
                      (prog:Programme)-[:HAS_UNITVARIANT]->(uv),
                      (eb:Examboard)-[:HAS_PROGRAMME]->(prog)
                WITH eb, uv, count{(uv)-[:HAS_LESSON]->(:Lesson)} AS lessons
                RETURN eb.examBoardTitle AS examBoard,
                       uv.optionTitle AS variant,
                       lessons
                ORDER BY examBoard
            `, { slug: unitSlug });

            return result.records.map(record => ({
                examBoard: record.get('examBoard'),
                variant: record.get('variant'),
                lessonCount: record.get('lessons').toNumber()
            }));
        } finally {
            await session.close();
        }
    }
}

// Usage
(async () => {
    const graph = new CurriculumGraph('bolt://localhost:7687', 'neo4j', 'password');
    
    // Get lesson details
    const lesson = await graph.getLessonDetails('understanding-the-poem-mild-the-mist-upon-the-hill');
    console.log('Lesson:', lesson.lessonTitle);
    console.log('Outcome:', lesson.pupilLessonOutcome);
    console.log('Keywords:', lesson.keywords.map(k => k.keyword).join(', '));
    
    // Compare exam boards
    const comparison = await graph.getExamBoardComparison('poetry-anthology-first-study');
    console.log('\nExam Board Comparison:');
    comparison.forEach(item => {
        console.log(`${item.examBoard}: ${item.lessonCount} lessons (${item.variant})`);
    });
    
    await graph.close();
})();
```

---

### Visualization Recommendations

**Neo4j Bloom:**
- Best for: Non-technical users exploring curriculum connections
- Use cases: Finding cross-curricular links, exploring unit relationships
- Setup: Import schema, create search phrases for common queries

**Neo4j Browser:**
- Best for: Technical users running ad-hoc queries
- Use cases: Data validation, query development, debugging
- Tips: Use `:style` command to customize node colors by type

**Custom Visualizations:**
- **D3.js:** For web-based interactive curriculum maps
- **Cytoscape.js:** For complex network analysis
- **vis.js:** For quick prototyping of graph visualizations

**Recommended Views:**
1. **Curriculum Map:** Subject → Unit → Lesson hierarchy
2. **Thread Network:** Units connected by shared threads
3. **Progression View:** Year-by-year skill development
4. **Exam Board Comparison:** Side-by-side qualification pathways

---

### Troubleshooting Common Issues

**Issue 1: Query Returns Too Many Results**
```cypher
// Problem: Unbounded query
MATCH (lesson:Lesson) RETURN lesson;  // Returns 12,631 rows!

// Solution: Add LIMIT or WHERE clause
MATCH (lesson:Lesson)
WHERE lesson.lessonTitle CONTAINS 'poetry'
RETURN lesson
LIMIT 20;
```

---

**Issue 2: Properties Appear as JSON Strings**

**Problem:** Keywords and learning points are stored as JSON string arrays.

**Solution:** Parse in application code:
```python
# Python
import json
keywords = [json.loads(k) for k in lesson['keywords']]
for kw in keywords:
    print(f"{kw['keyword']}: {kw['description']}")
```

```javascript
// JavaScript
const keywords = lesson.keywords.map(k => JSON.parse(k));
keywords.forEach(kw => {
    console.log(`${kw.keyword}: ${kw.description}`);
});
```

---

**Issue 3: Cannot Find Units for a Year/Subject**

**Problem:** Query returns no results.

**Diagnostic Query:**
```cypher
// Check if the year exists
MATCH (y:Year {yearTitle: "10"}) RETURN count(y);

// Check if the subject exists
MATCH (s:Subject {subjectSlug: "english"}) RETURN count(s);

// Check if unit offering exists
MATCH (y:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (s:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo)
RETURN count(uo);

// If count is 0, check available combinations
MATCH (y:Year)-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)<-[:HAS_UNIT_OFFERING]-(s:Subject)
RETURN y.yearTitle, s.subjectSlug
ORDER BY y.yearTitle, s.subjectSlug;
```

---

**Issue 4: Slow Query Performance**

**Diagnostic Steps:**
1. **Profile the query:**
   ```cypher
   PROFILE
   MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering)
   RETURN count(uo);
   ```

2. **Check for indexes:**
   ```cypher
   SHOW INDEXES;
   ```

3. **Create missing indexes:**
   ```cypher
   CREATE INDEX year_title IF NOT EXISTS FOR (y:Year) ON (y.yearTitle);
   ```

4. **Rewrite to start from most selective node:**
   ```cypher
   // Instead of starting from Lesson (12,631 nodes)
   MATCH (lesson:Lesson)<-[:HAS_LESSON]-(uv:Unitvariant)
   WHERE lesson.lessonTitle = "specific-title"
   
   // Start from the specific lesson
   MATCH (lesson:Lesson {lessonTitle: "specific-title"})
   MATCH (lesson)<-[:HAS_LESSON]-(uv:Unitvariant)
   ```

---

### Future Enhancements

**Planned Features:**
1. **Temporal Versioning:** Track curriculum changes over time
2. **Learning Objectives Taxonomy:** Hierarchical skill taxonomy
3. **Assessment Data:** Link to quiz results and student performance
4. **Resource Library:** Attach teaching materials, videos, worksheets
5. **Prerequisite Graph:** Explicit PREREQUISITE_FOR relationships
6. **Learning Path Recommendations:** Algorithm-based curriculum sequencing

**Enhancement Opportunities:**
- Add `:SIMILAR_TO` relationships between analogous lessons across subjects
- Include `:BUILDS_ON` relationships showing skill progression
- Model `:REQUIRES_RESOURCE` for equipment and materials
- Add `:TAUGHT_BY` relationships when linked to teacher data
- Create `:ASSESSED_BY` relationships to link quizzes

---

### Best Practices Summary

**Data Access:**
✅ Always use indexes for frequently queried properties
✅ Start queries from the most selective node
✅ Use parameters for reusable queries
✅ Limit results early in query execution
✅ Parse JSON properties in application code

**Query Design:**
✅ Use DISTINCT only when necessary
✅ Avoid unbounded variable-length paths
✅ Profile complex queries before production use
✅ Batch writes for bulk operations
✅ Use UNWIND for processing lists

**Application Integration:**
✅ Use connection pooling for better performance
✅ Handle JSON parsing consistently
✅ Cache frequently accessed data
✅ Implement retry logic for transient failures
✅ Close sessions and drivers properly

**Data Modeling:**
✅ Follow slug-based identifier patterns
✅ Maintain referential integrity
✅ Use junction nodes for many-to-many relationships
✅ Store rich metadata on leaf nodes
✅ Keep hierarchies shallow for query performance

---

## Quick Reference Card

**Most Common Queries:**

```cypher
// 1. List subjects
MATCH (s:Subject) RETURN s.subjectTitle ORDER BY s.displayOrder;

// 2. Find units for Year X and Subject Y
MATCH (year:Year {yearTitle: "10"})-[:HAS_UNIT_OFFERING]->(uo:Unitoffering),
      (subject:Subject {subjectSlug: "english"})-[:HAS_UNIT_OFFERING]->(uo),
      (uo)-[:HAS_UNIT]->(unit:Unit)
RETURN DISTINCT unit.unitTitle;

// 3. Get lesson details
MATCH (lesson:Lesson {lessonSlug: "lesson-slug"})
RETURN lesson;

// 4. Search by keyword
MATCH (lesson:Lesson)
WHERE any(kw IN lesson.keywords WHERE kw CONTAINS "search-term")
RETURN lesson.lessonTitle LIMIT 10;

// 5. Compare exam boards
MATCH (unit:Unit {unitSlug: "unit-slug"})-[:HAS_UNITVARIANT]->(uv:Unitvariant),
      (prog:Programme)-[:HAS_UNITVARIANT]->(uv),
      (eb:Examboard)-[:HAS_PROGRAMME]->(prog)
RETURN eb.examBoardTitle, count{(uv)-[:HAS_LESSON]->(:Lesson)} AS lessons;
```

**Key Patterns:**
- Year + Subject → Units: `(Year)-[:HAS_UNIT_OFFERING]->(:Unitoffering)<-[:HAS_UNIT_OFFERING]-(Subject)`
- Unit → Lessons: `(Unit)-[:HAS_UNITVARIANT]->(:Unitvariant)-[:HAS_LESSON]->(Lesson)`
- Exam Board → Programmes: `(Examboard)-[:HAS_PROGRAMME]->(Programme)-[:HAS_UNITVARIANT]->(Unitvariant)`

**Performance Tips:**
- Create indexes on: `yearTitle`, `subjectSlug`, `unitSlug`, `lessonSlug`, `examBoardSlug`
- Use LIMIT to restrict result sets
- Start queries from specific nodes, not broad scans
- Profile queries with PROFILE before optimization

---

**End of Documentation**

*For questions, issues, or contributions, please contact the Oak National Academy data team.*

