"""
Batch Hasura MV Data Export Module.

This module exports all data from multiple Hasura Materialized Views to CSV files.
Just specify the MV names - it gets ALL the data automatically.
"""

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv


@dataclass
class MVConfig:
    """Configuration for a single Materialized View."""
    name: str
    description: Optional[str] = None


@dataclass
class Config:
    """Application configuration."""

    HASURA_URL: str
    HASURA_TOKEN: str
    OUTPUT_DIR: Path = Path('data/exports')

    # List your MVs here - just the names!
    MVS: List[MVConfig] = None

    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        load_dotenv()
        hasura_url = os.getenv('HASURA_URL')
        hasura_token = os.getenv('HASURA_TOKEN')

        if not hasura_url:
            raise EnvironmentError("HASURA_URL environment variable not set")
        if not hasura_token:
            raise EnvironmentError("HASURA_TOKEN environment variable not set")

        # Configure your MVs here - just add the names!
        mvs = [
            MVConfig(
                name="published_mv_lesson_content_published_9_0_0"
            ),
            MVConfig(
                name="published_mv_synthetic_unitvariant_lessons_by_keystage_18_0_0"
            ),
            MVConfig(
                name="published_mv_synthetic_unitvariants_with_lesson_ids_by_keystage_18_0_0"
            ),
            MVConfig(
                name="published_mv_search_page_10_0_0"
            ),
            MVConfig(
                name="published_mv_key_stages_2_0_0"
            ),
            MVConfig(
                name="published_mv_curriculum_sequence_b_13_0_20"
            ),
        ]

        return cls(
            HASURA_URL=hasura_url,
            HASURA_TOKEN=hasura_token,
            MVS=mvs
        )


class HasuraClient:
    """Simple Hasura GraphQL client."""

    def __init__(self, url: str, token: str):
        self.url = url
        self.headers = {
            'Content-Type': 'application/json',
            'hasura-collaborator-token': token.strip()
        }

    def execute_query(self, query: str) -> Dict:
        """Execute GraphQL query."""
        try:
            response = requests.post(
                self.url,
                json={'query': query},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Query failed: {e}")
            return {}

    def get_all_data(self, mv_name: str) -> List[Dict]:
        """Get ALL data from an MV."""
        # Use introspection to discover the fields
        fields = self.get_fields_for_mv(mv_name)

        if not fields:
            print(f"Could not discover fields for {mv_name}")
            return []

        # Query all data with the discovered fields
        fields_str = "\n            ".join(fields)
        query = f"""
            query GetAllData {{
                {mv_name} {{
                    {fields_str}
                }}
            }}
        """

        response = self.execute_query(query)

        if 'errors' in response:
            print(f"Error querying {mv_name}: {response['errors']}")
            return []

        if 'data' not in response:
            print(f"No data returned for {mv_name}")
            return []

        # Get the data
        data = response['data']
        for key, value in data.items():
            if isinstance(value, list):
                return value

        return []

    def get_fields_for_mv(self, mv_name: str) -> List[str]:
        """Debug what's available and try to get fields for an MV."""
        # First, let's see what MVs are actually available
        simple_introspection = """
            query {
                __schema {
                    queryType {
                        fields {
                            name
                        }
                    }
                }
            }
        """

        response = self.execute_query(simple_introspection)

        if 'errors' in response or 'data' not in response:
            print(f"Introspection failed: {response}")
            return []

        available_fields = [f['name'] for f in response['data']['__schema']['queryType']['fields']]

        if mv_name not in available_fields:
            print(f"MV '{mv_name}' not found. Available fields:")
            for field in sorted(available_fields):
                if not field.startswith('__'):
                    print(f"  • {field}")
            return []

        # Now get the detailed schema for our specific MV
        detailed_introspection = f"""
            query {{
                __type(name: "{mv_name}") {{
                    fields {{
                        name
                    }}
                }}
            }}
        """

        response = self.execute_query(detailed_introspection)

        if 'data' in response and response['data']['__type'] and response['data']['__type']['fields']:
            return [f['name'] for f in response['data']['__type']['fields']]

        # If that doesn't work, try a different approach
        # Get the return type of the query field
        type_introspection = """
            query {
                __schema {
                    queryType {
                        fields {
                            name
                            type {
                                ofType {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        """

        response = self.execute_query(type_introspection)

        if 'data' in response:
            for field in response['data']['__schema']['queryType']['fields']:
                if field['name'] == mv_name:
                    type_name = field['type'].get('ofType', {}).get('name')
                    if type_name:
                        # Now get fields for this type
                        type_fields_query = f"""
                            query {{
                                __type(name: "{type_name}") {{
                                    fields {{
                                        name
                                    }}
                                }}
                            }}
                        """

                        type_response = self.execute_query(type_fields_query)
                        if 'data' in type_response and type_response['data']['__type']:
                            return [f['name'] for f in type_response['data']['__type']['fields']]

        return []


class BatchHasuraMVExporter:
    """Simple MV exporter."""

    def __init__(self, config: Config):
        self.config = config
        self.client = HasuraClient(config.HASURA_URL, config.HASURA_TOKEN)

        # Create output directory
        self.config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


    def export_all_mvs(self) -> None:
        """Export all configured MVs."""
        print(f"🚀 Exporting {len(self.config.MVS)} MVs to CSV...")

        for mv_config in self.config.MVS:
            print(f"📊 Exporting {mv_config.name}...")

            # Get all data
            data = self.client.get_all_data(mv_config.name)

            if not data:
                print(f"❌ No data found for {mv_config.name}")
                continue

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Clean up JSON columns
            for col in df.columns:
                if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                    df[col] = df[col].apply(
                        lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
                    )

            # Save to CSV
            filename = f"{mv_config.name}.csv"
            output_path = self.config.OUTPUT_DIR / filename
            df.to_csv(output_path, index=False)

            print(f"✅ Exported {len(df)} records to {filename}")

        print(f"\n📁 All files saved to: {self.config.OUTPUT_DIR}")


def main():
    """Main function."""
    try:
        config = Config.from_env()
        exporter = BatchHasuraMVExporter(config)
        exporter.export_all_mvs()
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()