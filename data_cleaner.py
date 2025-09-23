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
    def __init__(self, output_dir: str = "data", filters: Optional[dict] = None):
        self.output_dir = Path(output_dir)
        self.filters = filters or {}
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