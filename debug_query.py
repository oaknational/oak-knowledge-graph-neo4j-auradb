#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.extractors import HasuraExtractor

# Test the query building
fields = [
    "features",
    "is_legacy",
    "lesson_data",
    "lesson_slug",
    "null_unitvariant_id",
    "order_in_unit",
    "programme_fields",
    "programme_subject: programme_fields(path: \"programme_fields.subject\")",
    "programme_subject_id: programme_fields(path: \"programme_fields.subject_id\")",
    "programme_slug",
    "programme_slug_by_year",
    "static_lesson_list",
    "unit_data",
    "unit_slug",
    "unitvariant_id"
]

extractor = HasuraExtractor("dummy", "dummy")
query = extractor._build_graphql_query("published_mv_synthetic_unitvariant_lessons_by_keystage_18_0_0", fields, None)
print("Generated GraphQL Query:")
print(query)