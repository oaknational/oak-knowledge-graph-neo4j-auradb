#!/usr/bin/env python3
"""
JSON CSV Flattener - Expands all JSON fields in a CSV into separate columns.
"""

import pandas as pd
import json
import ast
from typing import Any, Dict, Set
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def safe_parse_json(value: Any) -> Any:
    """Safely parse a JSON string, handling various formats."""
    if pd.isna(value) or value == '' or value is None:
        return None

    if not isinstance(value, str):
        return value

    # Try to parse as JSON
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to parse as Python literal (handles single quotes)
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        pass

    # Return as-is if not parseable
    return value


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Handle lists by creating indexed keys
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))

    return dict(items)


def collect_all_json_keys(df: pd.DataFrame) -> Dict[str, Set[str]]:
    """Collect all possible keys from JSON columns across all rows."""
    logger.info("Analyzing JSON structure across all rows...")

    json_columns = {}

    for col in df.columns:
        logger.info(f"Analyzing column: {col}")
        all_keys = set()

        for idx, value in df[col].items():
            parsed = safe_parse_json(value)

            if isinstance(parsed, dict):
                flattened = flatten_dict(parsed)
                all_keys.update(flattened.keys())
            elif isinstance(parsed, list) and parsed:
                # Handle lists of objects
                for i, item in enumerate(parsed):
                    if isinstance(item, dict):
                        flattened = flatten_dict(item, f"[{i}]")
                        all_keys.update(flattened.keys())

        if all_keys:
            json_columns[col] = all_keys
            logger.info(f"  Found {len(all_keys)} unique keys in {col}")

    logger.info(f"Found JSON data in {len(json_columns)} columns")
    return json_columns


def expand_json_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Expand all JSON columns into separate columns."""
    logger.info(f"Starting with {len(df.columns)} columns and {len(df)} rows")

    # First pass: collect all possible keys from all rows
    json_columns = collect_all_json_keys(df)

    if not json_columns:
        logger.info("No JSON columns found")
        return df

    # Create new dataframe with expanded columns
    result_df = df.copy()

    for col_name, all_keys in json_columns.items():
        logger.info(f"Expanding column '{col_name}' into {len(all_keys)} new columns")

        # Create new columns for all keys
        new_cols = {}
        for key in sorted(all_keys):  # Sort for consistent ordering
            new_col_name = f"{col_name}.{key}"
            new_cols[new_col_name] = []

        # Process each row
        for idx, value in df[col_name].items():
            parsed = safe_parse_json(value)

            if isinstance(parsed, dict):
                flattened = flatten_dict(parsed)
            elif isinstance(parsed, list) and parsed:
                flattened = {}
                for i, item in enumerate(parsed):
                    if isinstance(item, dict):
                        item_flattened = flatten_dict(item, f"[{i}]")
                        flattened.update(item_flattened)
            else:
                flattened = {}

            # Add values to new columns
            for key in sorted(all_keys):
                new_col_name = f"{col_name}.{key}"
                new_cols[new_col_name].append(flattened.get(key, None))

        # Add new columns to result dataframe
        for new_col_name, values in new_cols.items():
            result_df[new_col_name] = values

        # Remove original JSON column
        result_df = result_df.drop(columns=[col_name])

    logger.info(f"Finished with {len(result_df.columns)} columns and {len(result_df)} rows")
    return result_df


def main():
    """Main function to process the CSV file."""
    input_file = "/Users/markhodierne/projects/oak/oak-knowledge-graph-neo4j-auradb/data/consolidated_data.csv"
    output_file = "/Users/markhodierne/projects/oak/oak-knowledge-graph-neo4j-auradb/data/consolidated_data_flattened.csv"

    logger.info(f"Reading CSV file: {input_file}")

    try:
        # Read CSV file
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")

        # Expand JSON columns
        expanded_df = expand_json_columns(df)

        # Save result
        logger.info(f"Saving flattened CSV to: {output_file}")
        expanded_df.to_csv(output_file, index=False, quoting=1)  # QUOTE_ALL for safety

        logger.info("✅ JSON flattening completed successfully!")
        logger.info(f"Original: {len(df.columns)} columns → Flattened: {len(expanded_df.columns)} columns")

    except Exception as e:
        logger.error(f"❌ Error processing CSV: {e}")
        raise


if __name__ == "__main__":
    main()