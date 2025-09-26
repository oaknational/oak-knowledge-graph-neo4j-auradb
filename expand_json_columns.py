#!/usr/bin/env python3
"""
Script to expand JSON columns in consolidated_data.csv
Expands top-level JSON fields into separate columns, keeping lists intact
Only goes 1 level deep as requested
"""

import pandas as pd
import ast
import sys
from typing import Any, Dict


def safe_dict_parse(dict_str: str) -> Dict[str, Any]:
    """Safely parse Python dictionary string, return empty dict if parsing fails"""
    if pd.isna(dict_str) or dict_str == "" or dict_str == "{}":
        return {}

    try:
        # Use ast.literal_eval to safely parse Python dictionary literals
        return ast.literal_eval(dict_str)
    except (ValueError, SyntaxError, TypeError):
        return {}


def expand_json_column_only(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Expand a JSON column into multiple columns with top-level keys only
    Returns ONLY the expanded columns (no original columns)

    Args:
        df: DataFrame containing the JSON column
        column_name: Name of the column containing JSON

    Returns:
        DataFrame with ONLY the expanded columns from the JSON field
    """
    if column_name not in df.columns:
        print(f"Warning: Column '{column_name}' not found in DataFrame")
        return pd.DataFrame()

    # Parse Python dictionary and extract top-level keys
    dict_data = df[column_name].apply(safe_dict_parse)

    # Get all unique top-level keys across all rows
    all_keys = set()
    for dict_obj in dict_data:
        if isinstance(dict_obj, dict):
            all_keys.update(dict_obj.keys())

    # Create new columns for each top-level key with proper naming
    expanded_columns = {}
    for key in sorted(all_keys):  # Sort for consistent column ordering
        col_name = f"{column_name}_{key}"
        expanded_columns[col_name] = dict_data.apply(
            lambda x: x.get(key) if isinstance(x, dict) else None
        )

    # Return ONLY the expanded DataFrame
    return pd.DataFrame(expanded_columns)


def create_expanded_csv(input_file: str, json_column: str, output_dir: str):
    """Create a separate CSV file with one JSON column expanded"""
    output_file = f"{output_dir}/expanded_{json_column}.csv"

    print(f"Processing {json_column} column...")

    # Read entire CSV at once (all rows)
    print(f"  Loading all rows from CSV...")
    df = pd.read_csv(input_file, low_memory=False)
    print(f"  Loaded {len(df)} rows")

    if json_column in df.columns:
        # Expand only this specific JSON column - return ONLY expanded columns
        print(f"  Expanding {json_column} column...")
        expanded_df = expand_json_column_only(df, json_column)
    else:
        print(f"  Warning: Column '{json_column}' not found")
        expanded_df = pd.DataFrame()

    print(f"  Saving expanded CSV to {output_file}...")
    expanded_df.to_csv(output_file, index=False)

    print(
        f"  ✅ {json_column}: {len(expanded_df.columns)} columns, {len(expanded_df)} rows"
    )
    return output_file


def main():
    input_file = "/Users/markhodierne/projects/oak/oak-knowledge-graph-neo4j-auradb/data/consolidated_data.csv"
    output_dir = (
        "/Users/markhodierne/projects/oak/oak-knowledge-graph-neo4j-auradb/data"
    )

    # JSON columns to expand
    json_columns = ["lesson_data", "programme_fields", "unit_data"]

    print("Creating separate CSV files for each JSON column expansion...")
    print("=" * 60)

    try:
        output_files = []

        for json_col in json_columns:
            # Check if column exists in the first chunk
            first_chunk = pd.read_csv(input_file, nrows=1)
            if json_col in first_chunk.columns:
                output_file = create_expanded_csv(input_file, json_col, output_dir)
                output_files.append(output_file)
                print()
            else:
                print(f"⚠️  Column '{json_col}' not found in CSV")

        print("=" * 60)
        print(f"✅ Successfully created {len(output_files)} expanded CSV files:")
        for file in output_files:
            print(f"   📄 {file}")

    except Exception as e:
        print(f"❌ Error processing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
