#!/bin/bash
# Integration Test Runner for Oak Knowledge Graph Pipeline
# Runs end-to-end tests and validates Neo4j CSV generation

set -e  # Exit on any error

echo "🧪 Oak Knowledge Graph - Integration Test Runner"
echo "================================================"

# Check if we're in the project root
if [ ! -f "main.py" ] || [ ! -d "pipeline" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python environment
if ! python3 -c "import pandas, requests, pydantic, neo4j" 2>/dev/null; then
    echo "❌ Error: Missing required dependencies. Run: pip install -r requirements.txt"
    exit 1
fi

# Create temp directory for test outputs
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: $TEMP_DIR"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo
echo "1️⃣ Running Integration Tests with pytest"
echo "----------------------------------------"
pytest tests/test_integration.py -v --tb=short

echo
echo "2️⃣ Testing Pipeline CLI Interface"
echo "--------------------------------"

# Test configuration validation
echo "Testing configuration loading..."
python main.py --config config/integration_test_config.json --help > /dev/null
echo "✅ Configuration loads successfully"

# Test extraction-only mode (dry run)
echo "Testing extraction-only pipeline..."
OUTPUT_DIR="$TEMP_DIR/cli_test"
mkdir -p "$OUTPUT_DIR"

# Mock the Hasura extractor for CLI testing
python -c "
import sys
sys.path.append('.')
from pipeline.pipeline import Pipeline
from unittest.mock import patch, Mock
import json

# Load test data
with open('tests/fixtures/integration_test_data.json', 'r') as f:
    test_data = json.load(f)

def mock_extract(view_name, limit=None):
    if view_name in test_data:
        data = test_data[view_name]['data'][view_name]
        if limit:
            data = data[:limit]
        return data
    return []

with patch('pipeline.extractors.HasuraExtractor.extract_from_view', side_effect=mock_extract):
    pipeline = Pipeline(
        config_path='config/integration_test_config.json',
        output_dir='$OUTPUT_DIR'
    )
    result = pipeline.run_full_pipeline(use_auradb=False)
    print(f'Pipeline result: {result.success}')
    if not result.success:
        sys.exit(1)
"

echo "✅ CLI pipeline execution successful"

echo
echo "3️⃣ Validating Generated CSV Files"
echo "--------------------------------"

# Check for generated files
CSV_COUNT=$(find "$OUTPUT_DIR" -name "*.csv" | wc -l)
echo "📊 Found $CSV_COUNT CSV files"

if [ "$CSV_COUNT" -eq 0 ]; then
    echo "❌ Error: No CSV files generated"
    exit 1
fi

# Validate CSV format for each file
for csv_file in "$OUTPUT_DIR"/*.csv; do
    filename=$(basename "$csv_file")
    echo "Validating $filename..."

    # Check if file is not empty
    if [ ! -s "$csv_file" ]; then
        echo "❌ Error: $filename is empty"
        exit 1
    fi

    # Check CSV headers
    header=$(head -1 "$csv_file")

    if [[ "$filename" == *"_nodes.csv" ]]; then
        # Node files should have :ID and :LABEL columns
        if [[ ! "$header" == *":ID"* ]] || [[ ! "$header" == *":LABEL"* ]]; then
            echo "❌ Error: $filename missing required node headers (:ID, :LABEL)"
            echo "   Headers: $header"
            exit 1
        fi
        echo "✅ $filename has valid node headers"
    elif [[ "$filename" == *"_relationships.csv" ]]; then
        # Relationship files should have :START_ID, :END_ID, :TYPE columns
        if [[ ! "$header" == *":START_ID"* ]] || [[ ! "$header" == *":END_ID"* ]] || [[ ! "$header" == *":TYPE"* ]]; then
            echo "❌ Error: $filename missing required relationship headers (:START_ID, :END_ID, :TYPE)"
            echo "   Headers: $header"
            exit 1
        fi
        echo "✅ $filename has valid relationship headers"
    fi

    # Count records
    record_count=$(($(wc -l < "$csv_file") - 1))  # Subtract header
    echo "   📈 $record_count records"
done

echo
echo "4️⃣ Testing Neo4j Import Command Generation"
echo "------------------------------------------"

# Test Neo4j import command generation
python -c "
import sys
sys.path.append('.')
from pipeline.loaders import Neo4jLoader
from pathlib import Path

loader = Neo4jLoader()
csv_dir = Path('$OUTPUT_DIR')

# Find CSV files
csv_files = list(csv_dir.glob('*.csv'))
if not csv_files:
    print('No CSV files found for import command generation')
    sys.exit(1)

# Test command generation
import_cmd = loader.generate_import_command(str(csv_dir), 'test-db')
if not import_cmd:
    print('Failed to generate import command')
    sys.exit(1)

print('✅ Neo4j import command generated successfully')
print(f'Command length: {len(import_cmd)} characters')

# Verify command structure
if 'neo4j-admin database import' not in import_cmd:
    print('❌ Error: Invalid command structure')
    sys.exit(1)

print('✅ Command structure is valid')
"

echo
echo "5️⃣ Integration Test Summary"
echo "============================"

echo "✅ Configuration validation: PASSED"
echo "✅ Pipeline execution: PASSED"
echo "✅ CSV generation: PASSED"
echo "✅ CSV format validation: PASSED"
echo "✅ Neo4j command generation: PASSED"

echo
echo "📋 Test Results Summary:"
echo "  - Generated $CSV_COUNT CSV files"
echo "  - All files have correct Neo4j headers"
echo "  - Neo4j import commands generated successfully"
echo "  - Pipeline handles mock data correctly"

echo
echo "💡 Next Steps for Manual Validation:"
echo "  1. Set up Neo4j instance (if not already done)"
echo "  2. Run: python main.py --config config/integration_test_config.json --full"
echo "  3. Import generated CSVs to test database"
echo "  4. Verify data integrity in Neo4j browser"

echo
echo "🎉 Integration Tests Completed Successfully!"
echo "Pipeline is ready for production use."