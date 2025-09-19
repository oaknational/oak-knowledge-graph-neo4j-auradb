#!/usr/bin/env python3
"""
Debug script to see what fields are actually in the extracted data.
"""

from dotenv import load_dotenv
from pipeline.pipeline import Pipeline
from pipeline.config_manager import ConfigManager

load_dotenv()

def main():
    # Initialize pipeline
    config_manager = ConfigManager()
    pipeline = Pipeline(config_manager=config_manager)

    # Load config and extract data
    config = pipeline.load_config("oak_curriculum_schema_v0.1.0-alpha.json")
    extracted_data = pipeline.extract_data()

    print(f"✅ Extracted {len(extracted_data)} records")

    if extracted_data:
        # Show first record structure
        first_record = extracted_data[0]
        print(f"\n🔍 First record fields:")
        for field, value in first_record.items():
            value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"  {field}: {value_str}")

        # Show unique field names across all records
        all_fields = set()
        for record in extracted_data:
            all_fields.update(record.keys())

        print(f"\n📋 All unique fields found ({len(all_fields)} total):")
        for field in sorted(all_fields):
            print(f"  - {field}")

if __name__ == "__main__":
    main()