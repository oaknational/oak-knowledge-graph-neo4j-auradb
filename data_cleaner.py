import pandas as pd
from pathlib import Path
from typing import Optional
import logging


class DataCleaner:
    """
    Optional data cleaning and preprocessing component.

    This provides an area where you can add custom data cleaning logic
    to transform the consolidated CSV before schema mapping.
    """

    def __init__(
        self,
        output_dir: str = "data",
        filters: Optional[dict] = None,
        schema_mapping: Optional[dict] = None,
        array_expansion: Optional[dict] = None,
    ):
        self.output_dir = Path(output_dir)
        self.filters = filters or {}
        self.schema_mapping = schema_mapping or {}
        self.array_expansion = array_expansion or {}
        self.logger = logging.getLogger(__name__)

    def clean_data(self, csv_file_path: str) -> str:
        """
        Apply data cleaning transformations to the CSV file.

        Args:
            csv_file_path: Path to the consolidated CSV file

        Returns:
            Path to the cleaned CSV file
        """
        self.logger.info(f"Starting data cleaning on {csv_file_path}")

        # Load the CSV
        try:
            df = pd.read_csv(csv_file_path)
            self.logger.info(
                f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns"
            )
        except Exception as e:
            self.logger.error(f"Failed to load CSV file {csv_file_path}: {e}")
            raise

        # Apply cleaning transformations
        df_cleaned = self._apply_cleaning_transformations(df)

        # Save cleaned CSV
        cleaned_file_path = self._get_cleaned_file_path(csv_file_path)
        try:
            df_cleaned.to_csv(cleaned_file_path, index=False)
            self.logger.info(f"Saved cleaned CSV to {cleaned_file_path}")
            self.logger.info(
                f"Cleaned CSV has {len(df_cleaned)} rows and "
                f"{len(df_cleaned.columns)} columns"
            )
        except Exception as e:
            self.logger.error(f"Failed to save cleaned CSV: {e}")
            raise

        return str(cleaned_file_path)

    def _apply_cleaning_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply data cleaning transformations.

        ADD YOUR CUSTOM CLEANING LOGIC HERE:
        - Remove duplicates
        - Handle missing values
        - Standardize data formats
        - Apply business rules
        - Transform column values

        This is the area where you can customize data preprocessing.
        """
        df_cleaned = df.copy()

        # Remove empty rows
        df_cleaned = df_cleaned.dropna(how="all")
        self.logger.info(f"Removed empty rows, now have {len(df_cleaned)} rows")

        # Strip whitespace
        for col in df_cleaned.select_dtypes(include=["object"]).columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()

        # Apply filters (if defined in config)
        df_cleaned = self._filter_data(df_cleaned)

        # Skip JSON array unpacking - now handled just-in-time by SchemaMapper
        self.logger.info("Skipping JSON array unpacking - handled just-in-time by SchemaMapper")

        # Generate synthetic columns (if defined in schema)
        df_cleaned = self._generate_synthetic_columns(df_cleaned)

        # Add current timestamp for lastUpdated property
        from datetime import datetime

        current_timestamp = datetime.now().isoformat()
        df_cleaned["current_timestamp"] = current_timestamp
        self.logger.info(f"Added current timestamp column: {current_timestamp}")

        self.logger.info("Applied data cleaning transformations")
        return df_cleaned

    def _filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.filters:
            self.logger.info("No filters provided; skipping filtering step")
            return df

        filtered_df = df.copy()
        for col, value in self.filters.items():
            if col not in filtered_df.columns:
                self.logger.warning(f"Filter column '{col}' not found in DataFrame")
                continue

            if isinstance(value, list):  # multiple allowed values
                filtered_df = filtered_df[filtered_df[col].isin(value)]
                self.logger.info(
                    f"Applied filter: {col} in {value}, {len(filtered_df)} rows remain"
                )
            else:  # single value
                filtered_df = filtered_df[filtered_df[col] == value]
                self.logger.info(
                    f"Applied filter: {col} == {value}, {len(filtered_df)} rows remain"
                )

        return filtered_df

    def _unpack_json_arrays(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Automatically detect and unpack JSON arrays in any column.

        For each column containing JSON arrays like:
        [{"key": "value1"}, {"key": "value2"}]

        Creates new rows for each array item and flattens the JSON objects.
        """
        import json

        df_unpacked = df.copy()
        unpacked_any = False

        for col in df_unpacked.columns:
            # Only unpack arrays that are configured for expansion
            if col in self.array_expansion and self.array_expansion[col]:
                if self._column_contains_json_arrays(df_unpacked[col]):
                    self.logger.info(f"Unpacking JSON arrays in column: {col}")
                    df_unpacked = self._unpack_column_arrays(df_unpacked, col)
                    unpacked_any = True
                else:
                    self.logger.info(f"Column {col} configured for expansion but contains no JSON arrays")
            elif self._column_contains_json_arrays(df_unpacked[col]):
                self.logger.info(f"Skipping JSON array expansion for column: {col} (not configured)")

        if unpacked_any:
            self.logger.info(f"After unpacking arrays: {len(df_unpacked)} rows")

        return df_unpacked

    def _column_contains_json_arrays(self, series: pd.Series) -> bool:
        """Check if a column contains JSON arrays by sampling non-null values."""
        import ast
        import json

        # Sample a few non-null values to check for JSON arrays
        non_null_values = series.dropna().head(10)

        for value in non_null_values:
            try:
                if isinstance(value, str) and value.strip().startswith('['):
                    # Try JSON first (double quotes)
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            return True
                    except json.JSONDecodeError:
                        # Try Python literal evaluation (single quotes)
                        try:
                            parsed = ast.literal_eval(value)
                            if isinstance(parsed, list) and len(parsed) > 0:
                                return True
                        except (ValueError, SyntaxError):
                            continue
            except AttributeError:
                continue

        return False

    def _unpack_column_arrays(self, df: pd.DataFrame, array_col: str) -> pd.DataFrame:
        """Unpack a specific column containing JSON arrays."""
        import ast
        import json

        unpacked_rows = []

        for idx, row in df.iterrows():
            array_value = row[array_col]

            # Skip if null or not a string
            if pd.isna(array_value) or not isinstance(array_value, str):
                unpacked_rows.append(row.to_dict())
                continue

            try:
                # Try JSON first (double quotes)
                parsed_array = None
                try:
                    parsed_array = json.loads(array_value)
                except json.JSONDecodeError:
                    # Try Python literal evaluation (single quotes)
                    try:
                        parsed_array = ast.literal_eval(array_value)
                    except (ValueError, SyntaxError):
                        # Not parseable - keep original row
                        unpacked_rows.append(row.to_dict())
                        continue

                if isinstance(parsed_array, list) and len(parsed_array) > 0:
                    # Create a row for each array item
                    for item in parsed_array:
                        new_row = row.to_dict()

                        if isinstance(item, dict):
                            # Flatten the dict object into separate columns
                            for key, value in item.items():
                                # Use a naming convention: original_col_key
                                new_col_name = f"{array_col}_{key}"
                                new_row[new_col_name] = value
                        else:
                            # If array contains primitives, use the item directly
                            new_row[array_col] = item

                        unpacked_rows.append(new_row)
                else:
                    # Empty array or not an array - keep original row
                    unpacked_rows.append(row.to_dict())

            except Exception as e:
                self.logger.warning(f"Failed to parse array in {array_col}: {e}")
                # Keep original row on any error
                unpacked_rows.append(row.to_dict())

        return pd.DataFrame(unpacked_rows)

    def _generate_synthetic_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate synthetic columns based on schema mapping configuration."""
        if not self.schema_mapping or "nodes" not in self.schema_mapping:
            return df

        df_with_synthetic = df.copy()

        # Find all synthetic nodes in the schema
        nodes = self.schema_mapping.get("nodes", {})

        for node_label, node_config in nodes.items():
            id_field_config = node_config.get("id_field", {})
            synthetic_value = id_field_config.get("synthetic_value", "")
            hasura_col = id_field_config.get("hasura_col", "")

            if synthetic_value:
                # Handle completely synthetic nodes (no hasura_col)
                if not hasura_col:
                    # Generate column name for synthetic values
                    property_name = id_field_config.get("property_name", "id")
                    hasura_col = property_name

                self.logger.info(
                    f"Generating synthetic column '{hasura_col}' for {node_label} nodes"
                )

                # Generate synthetic IDs using synthetic_value
                synthetic_ids = []
                for _, row in df_with_synthetic.iterrows():
                    synthetic_id = self._generate_synthetic_id(row, synthetic_value)
                    synthetic_ids.append(synthetic_id if synthetic_id else "")

                # Add the synthetic column
                df_with_synthetic[hasura_col] = synthetic_ids
                count = len([id for id in synthetic_ids if id])
                self.logger.info(
                    f"Generated {count} synthetic IDs for column '{hasura_col}'"
                )

        return df_with_synthetic

    def _generate_synthetic_id(self, row: pd.Series, synthetic_value: str) -> str:
        """Generate synthetic ID using synthetic_value substitution."""
        try:
            # Check if synthetic_value contains placeholders for dynamic generation
            if "{" in synthetic_value and "}" in synthetic_value:
                # Replace placeholders in synthetic_value with actual row values
                result_id = synthetic_value

                # Find all {field_name} placeholders in the synthetic_value
                import re

                placeholders = re.findall(r"\{([^}]+)\}", synthetic_value)

                for placeholder in placeholders:
                    if placeholder in row and pd.notna(row[placeholder]):
                        value = str(row[placeholder]).strip()
                        result_id = result_id.replace(f"{{{placeholder}}}", value)
                    else:
                        # If any required field is missing, return None
                        return None

                return result_id
            else:
                # Static synthetic value - return as is
                return synthetic_value

        except Exception as e:
            self.logger.error(
                f"Failed to generate synthetic ID with "
                f"synthetic_value '{synthetic_value}': {e}"
            )
            return None

    def _get_cleaned_file_path(self, original_file_path: str) -> Path:
        """Generate file path for cleaned CSV."""
        original_path = Path(original_file_path)
        cleaned_filename = f"{original_path.stem}_cleaned{original_path.suffix}"
        return self.output_dir / cleaned_filename

    def skip_cleaning(self, csv_file_path: str) -> str:
        """
        Skip cleaning and return the original file path.
        Useful when no cleaning is needed.
        """
        self.logger.info("Skipping data cleaning - returning original file")
        return csv_file_path
