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

    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
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

        # Example cleaning operations (customize as needed):

        # 1. Remove completely empty rows
        df_cleaned = df_cleaned.dropna(how='all')
        self.logger.info(f"Removed empty rows, now have {len(df_cleaned)} rows")

        # 2. Strip whitespace from string columns
        for col in df_cleaned.select_dtypes(include=['object']).columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()

        # 3. Example: Remove test/placeholder data (customize the condition)
        # df_cleaned = df_cleaned[~df_cleaned['title'].str.contains('test', case=False, na=False)]

        # 4. Example: Standardize boolean values
        # for col in ['is_active', 'published']:  # Customize column names
        #     if col in df_cleaned.columns:
        #         df_cleaned[col] = df_cleaned[col].astype(str).str.lower().map({
        #             'true': True, '1': True, 'yes': True,
        #             'false': False, '0': False, 'no': False
        #         })

        # 5. Example: Handle missing values with defaults
        # df_cleaned['description'] = df_cleaned['description'].fillna('No description available')

        # 6. Example: Remove duplicates based on specific columns
        # df_cleaned = df_cleaned.drop_duplicates(subset=['id', 'title'], keep='first')

        self.logger.info("Applied basic data cleaning transformations")
        return df_cleaned

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