#!/usr/bin/env python3
"""
Test HasuraExtractor with real Oak curriculum data
"""
import os
from dotenv import load_dotenv
from pipeline.extractors import HasuraExtractor
from models.config import PipelineConfig

load_dotenv()

def test_real_extraction():
    print("Testing HasuraExtractor with real Oak data...")

    # Initialize extractor
    try:
        extractor = HasuraExtractor()
        print("✅ HasuraExtractor initialized with Oak authentication")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False

    # Test with a small sample
    config = PipelineConfig(
        hasura_endpoint=os.getenv("HASURA_ENDPOINT"),
        materialized_views=["published_mv_key_stages_2_0_0"],  # Start with smallest
        node_mappings=[],
        relationship_mappings=[]
    )

    try:
        print(f"\nExtracting from: {config.materialized_views[0]}")
        data = extractor.extract(config)

        print(f"✅ Successfully extracted {len(data)} records")

        if data:
            print("\n📄 Sample record:")
            sample = data[0]
            for key, value in list(sample.items())[:5]:  # Show first 5 fields
                print(f"   {key}: {value}")

            if len(sample) > 5:
                print(f"   ... and {len(sample) - 5} more fields")

        return True

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

if __name__ == "__main__":
    success = test_real_extraction()
    if success:
        print("\n🎉 Real data extraction test successful!")
        print("The HasuraExtractor is ready for the full pipeline.")
    else:
        print("\n❌ Real data extraction test failed.")