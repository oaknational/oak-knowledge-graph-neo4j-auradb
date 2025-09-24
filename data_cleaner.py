import pandas as pd
import os
from pathlib import Path
from typing import Optional
import logging


class DataCleaner:
    """
    Optional data cleaning and preprocessing component.

    This provides an area where you can add custom data cleaning logic
    to transform the consolidated CSV before schema mapping.
    """
    def __init__(self, output_dir: str = "data", filters: Optional[dict] = None, schema_mapping: Optional[dict] = None):
        self.output_dir = Path(output_dir)
        self.filters = filters or {}
        self.schema_mapping = schema_mapping or {}
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
            self.logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
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
            self.logger.info(f"Cleaned CSV has {len(df_cleaned)} rows and {len(df_cleaned.columns)} columns")
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
        df_cleaned = df_cleaned.dropna(how='all')
        self.logger.info(f"Removed empty rows, now have {len(df_cleaned)} rows")

        # Strip whitespace
        for col in df_cleaned.select_dtypes(include=['object']).columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
            
        # Apply filters (if defined in config)
        df_cleaned = self._filter_data(df_cleaned)

        # Generate synthetic columns (if defined in schema)
        df_cleaned = self._generate_synthetic_columns(df_cleaned)

        # Add current timestamp for lastUpdated property
        from datetime import datetime
        current_timestamp = datetime.now().isoformat()
        df_cleaned['current_timestamp'] = current_timestamp
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

    def _generate_synthetic_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate synthetic columns based on schema mapping configuration."""
        if not self.schema_mapping or "nodes" not in self.schema_mapping:
            return df

        df_with_synthetic = df.copy()

        # Find all synthetic nodes in the schema
        nodes = self.schema_mapping.get("nodes", {})

        for node_label, node_config in nodes.items():
            id_field_config = node_config.get("id_field", {})
            is_synthetic = id_field_config.get("synthetic", False)
            pattern = id_field_config.get("pattern", "")
            hasura_col = id_field_config.get("hasura_col", "")

            if is_synthetic and pattern and hasura_col:
                self.logger.info(f"Generating synthetic column '{hasura_col}' for {node_label} nodes")

                # Generate synthetic IDs using pattern
                synthetic_ids = []
                for _, row in df_with_synthetic.iterrows():
                    synthetic_id = self._generate_synthetic_id(row, pattern)
                    synthetic_ids.append(synthetic_id if synthetic_id else "")

                # Add the synthetic column
                df_with_synthetic[hasura_col] = synthetic_ids
                self.logger.info(f"Generated {len([id for id in synthetic_ids if id])} synthetic IDs for column '{hasura_col}'")

        return df_with_synthetic

    def _generate_synthetic_id(self, row: pd.Series, pattern: str) -> str:
        """Generate synthetic ID using pattern substitution."""
        try:
            # Replace placeholders in pattern with actual row values
            synthetic_id = pattern

            # Find all {field_name} placeholders in the pattern
            import re
            placeholders = re.findall(r'\{([^}]+)\}', pattern)

            for placeholder in placeholders:
                if placeholder in row and pd.notna(row[placeholder]):
                    value = str(row[placeholder]).strip()
                    synthetic_id = synthetic_id.replace(f"{{{placeholder}}}", value)
                else:
                    # If any required field is missing, return None
                    return None

            return synthetic_id
        except Exception as e:
            self.logger.error(f"Failed to generate synthetic ID with pattern '{pattern}': {e}")
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