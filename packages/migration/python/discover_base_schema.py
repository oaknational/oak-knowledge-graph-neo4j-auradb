#!/usr/bin/env python3
"""
Discover Actual PostgreSQL Base Table Schema

This script analyzes Hasura GraphQL to identify the actual underlying PostgreSQL
base tables (not views/computed tables) and their real column structure and relationships.

Filters out:
- Materialized views (published_mv_*)
- Computed views (published_view_*)
- Aggregation types (*_aggregate, *_avg_fields, etc.)
- Versioned views (*_by_year_*, *_by_keystage_*)

Focuses on discovering:
- Actual base PostgreSQL tables
- Real column fields and data types
- Foreign key relationships
- Table relationships and dependencies
"""

import os
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import re

import click
from rich.console import Console
from rich.table import Table
from rich.progress import track, Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from dotenv import load_dotenv
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# Load environment variables
load_dotenv()

console = Console()

@dataclass
class BaseTableField:
    """Information about a field in a base PostgreSQL table."""
    name: str
    type: str
    is_nullable: bool
    is_foreign_key: bool = False
    references_table: Optional[str] = None
    references_field: Optional[str] = None

@dataclass
class BaseTable:
    """Information about a base PostgreSQL table."""
    name: str
    fields: List[BaseTableField]
    estimated_rows: Optional[int] = None
    relationships: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []

@dataclass
class BaseSchemaAnalysis:
    """Analysis of actual PostgreSQL base tables."""
    endpoint: str
    analyzed_at: datetime
    base_tables: List[BaseTable]
    relationships: List[Dict[str, Any]]
    summary: Dict[str, Any]

class BaseSchemaDiscoverer:
    """Discovers actual PostgreSQL base tables behind Hasura GraphQL."""
    
    def __init__(self, endpoint: str, admin_secret: Optional[str] = None):
        self.endpoint = endpoint
        self.admin_secret = admin_secret
        self.client = None
        
    def connect(self) -> None:
        """Connect to Hasura GraphQL endpoint."""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Hasura-Client-Name': 'base-schema-discoverer'
            }
            
            if self.admin_secret:
                headers["hasura-collaborator-token"] = self.admin_secret.strip()
            
            transport = AIOHTTPTransport(
                url=self.endpoint,
                headers=headers,
                timeout=30
            )
            
            self.client = Client(transport=transport)
            console.print("✅ Connected to Hasura GraphQL endpoint", style="green")
            
        except Exception as e:
            console.print(f"❌ Failed to connect: {e}", style="red")
            raise
    
    def introspect_schema(self) -> Dict[str, Any]:
        """Get full GraphQL schema via introspection."""
        introspection_query = gql("""
            query IntrospectionQuery {
                __schema {
                    types {
                        name
                        description
                        kind
                        fields {
                            name
                            description
                            type {
                                name
                                kind
                                ofType {
                                    name
                                    kind
                                    ofType {
                                        name
                                        kind
                                        ofType {
                                            name
                                            kind
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """)
        
        try:
            result = self.client.execute(introspection_query)
            return result["__schema"]
        except Exception as e:
            console.print(f"❌ Schema introspection failed: {e}", style="red")
            raise
    
    def identify_base_tables(self, schema_types: List[Dict]) -> List[str]:
        """
        Filter schema types to identify actual base PostgreSQL tables.
        Excludes computed views, aggregations, and materialized views.
        """
        
        # Patterns that indicate computed/derived types (NOT base tables)
        exclude_patterns = [
            # Aggregation types
            '_aggregate', '_aggregate_fields', '_avg_fields', '_max_fields', 
            '_min_fields', '_stddev_fields', '_stddev_pop_fields', 
            '_stddev_samp_fields', '_sum_fields', '_var_pop_fields', 
            '_var_samp_fields', '_variance_fields',
            
            # Computed/materialized views
            'published_mv_', 'published_view_', 
            
            # Versioned/filtered views
            '_by_year_', '_by_keystage_', '_canonical_', '_browse_',
            '_synthetic_', '_redirects_', '_openapi_',
            
            # System types
            '__', 'query_root', 'mutation_root', 'subscription_root'
        ]
        
        # Get object types only (tables/views)
        object_types = [
            t for t in schema_types 
            if t.get("kind") == "OBJECT" and not t["name"].startswith("__")
        ]
        
        base_tables = []
        excluded_count = 0
        
        for type_info in object_types:
            type_name = type_info["name"]
            
            # Check if this type should be excluded
            is_excluded = any(pattern in type_name for pattern in exclude_patterns)
            
            if is_excluded:
                excluded_count += 1
                continue
                
            # Additional filtering: must have fields
            if not type_info.get("fields"):
                excluded_count += 1
                continue
                
            base_tables.append(type_name)
        
        console.print(f"Found {len(base_tables)} base tables, excluded {excluded_count} computed types", style="cyan")
        return base_tables
    
    def parse_graphql_type(self, type_info: Dict[str, Any]) -> str:
        """Parse GraphQL type info to readable string."""
        if not type_info:
            return "Unknown"
            
        kind = type_info.get("kind", "")
        name = type_info.get("name", "")
        of_type = type_info.get("ofType")
        
        if kind == "NON_NULL":
            return self.parse_graphql_type(of_type)
        elif kind == "LIST":
            return f"[{self.parse_graphql_type(of_type)}]"
        elif name:
            return name
        else:
            return "Unknown"
    
    def detect_foreign_key(self, field_name: str, field_type: str, known_tables: Set[str]) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Detect if a field is likely a foreign key based on naming patterns.
        Returns: (is_foreign_key, referenced_table, referenced_field)
        """
        
        # Common foreign key patterns
        if field_name.endswith('_id') and field_type in ['ID', 'String', 'Int', 'uuid']:
            # Extract potential table name
            table_part = field_name[:-3]  # Remove '_id'
            
            # Try different table naming patterns
            potential_tables = [
                table_part,           # lesson_id -> lesson
                f"{table_part}s",     # lesson_id -> lessons  
                table_part.replace('_', ''),  # unit_variant_id -> unitvariant
                f"pf_{table_part}s",  # subject_id -> pf_subjects
                f"cat_{table_part}",  # category_id -> cat_category
            ]
            
            for potential_table in potential_tables:
                if potential_table in known_tables:
                    return True, potential_table, "id"
        
        # Handle specific Oak curriculum patterns
        oak_fk_patterns = {
            'programme_slug': ('programmes', 'slug'),
            'subject_slug': ('pf_subjects', 'slug'), 
            'unit_slug': ('units', 'slug'),
            'lesson_slug': ('lessons', 'slug'),
            'thread_slug': ('programme_threads', 'slug')
        }
        
        if field_name in oak_fk_patterns and field_type in ['String', 'ID']:
            table, field = oak_fk_patterns[field_name]
            if table in known_tables:
                return True, table, field
        
        return False, None, None
    
    def analyze_base_table(self, table_name: str, type_info: Dict, known_tables: Set[str]) -> BaseTable:
        """Analyze a single base table to extract field information."""
        
        fields = []
        
        for field_info in type_info.get("fields", []):
            field_name = field_info["name"]
            field_type_raw = field_info["type"]
            field_type = self.parse_graphql_type(field_type_raw)
            is_nullable = field_type_raw.get("kind") != "NON_NULL"
            
            # Detect if this field is a foreign key
            is_fk, ref_table, ref_field = self.detect_foreign_key(field_name, field_type, known_tables)
            
            field = BaseTableField(
                name=field_name,
                type=field_type,
                is_nullable=is_nullable,
                is_foreign_key=is_fk,
                references_table=ref_table,
                references_field=ref_field
            )
            fields.append(field)
        
        # Try to get row count estimate
        estimated_rows = self.get_table_row_count(table_name)
        
        return BaseTable(
            name=table_name,
            fields=fields,
            estimated_rows=estimated_rows
        )
    
    def get_table_row_count(self, table_name: str) -> Optional[int]:
        """Get estimated row count for a table."""
        try:
            query = gql(f"""
                query {{
                    {table_name}_aggregate {{
                        aggregate {{
                            count
                        }}
                    }}
                }}
            """)
            
            result = self.client.execute(query)
            return result[f"{table_name}_aggregate"]["aggregate"]["count"]
            
        except Exception:
            # Many base tables might not have aggregate queries exposed
            return None
    
    def extract_relationships(self, base_tables: List[BaseTable]) -> List[Dict[str, Any]]:
        """Extract relationships between base tables based on foreign keys."""
        
        relationships = []
        
        for table in base_tables:
            for field in table.fields:
                if field.is_foreign_key and field.references_table:
                    relationships.append({
                        "from_table": table.name,
                        "from_field": field.name,
                        "to_table": field.references_table,
                        "to_field": field.references_field or "id",
                        "relationship_type": "BELONGS_TO" if field.name.endswith('_id') else "REFERENCES"
                    })
        
        return relationships
    
    def discover_base_schema(self) -> BaseSchemaAnalysis:
        """Perform complete base schema discovery."""
        
        console.print("🔍 Discovering actual PostgreSQL base table schema...", style="bold blue")
        
        # Get full schema
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running GraphQL introspection...", total=None)
            schema = self.introspect_schema()
            progress.remove_task(task)
        
        # Identify base tables (exclude computed views)
        base_table_names = self.identify_base_tables(schema["types"])
        console.print(f"📊 Identified {len(base_table_names)} base tables", style="green")
        
        # Analyze each base table
        type_lookup = {t["name"]: t for t in schema["types"]}
        known_tables = set(base_table_names)
        base_tables = []
        
        for table_name in track(base_table_names, description="Analyzing base tables..."):
            type_info = type_lookup.get(table_name)
            if type_info:
                base_table = self.analyze_base_table(table_name, type_info, known_tables)
                base_tables.append(base_table)
        
        # Extract relationships
        relationships = self.extract_relationships(base_tables)
        
        # Create summary
        tables_with_data = [t for t in base_tables if t.estimated_rows and t.estimated_rows > 0]
        total_estimated_rows = sum(t.estimated_rows for t in tables_with_data if t.estimated_rows)
        
        # Find tables with most foreign keys (likely central entities)
        fk_counts = {}
        for table in base_tables:
            fk_count = sum(1 for f in table.fields if f.is_foreign_key)
            if fk_count > 0:
                fk_counts[table.name] = fk_count
        
        summary = {
            "total_base_tables": len(base_tables),
            "tables_with_data": len(tables_with_data),
            "total_estimated_rows": total_estimated_rows,
            "total_relationships": len(relationships),
            "largest_tables": sorted(
                [(t.name, t.estimated_rows) for t in tables_with_data],
                key=lambda x: x[1] or 0,
                reverse=True
            )[:10],
            "most_connected_tables": sorted(
                fk_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }
        
        return BaseSchemaAnalysis(
            endpoint=self.endpoint,
            analyzed_at=datetime.now(),
            base_tables=base_tables,
            relationships=relationships,
            summary=summary
        )
    
    def save_analysis(self, analysis: BaseSchemaAnalysis, output_file: str) -> None:
        """Save base schema analysis to JSON file."""
        
        # Convert to dict for JSON serialization
        analysis_dict = asdict(analysis)
        analysis_dict["analyzed_at"] = analysis.analyzed_at.isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_dict, f, indent=2, ensure_ascii=False)
        
        console.print(f"💾 Base schema analysis saved to: {output_file}", style="green")
    
    def print_analysis_summary(self, analysis: BaseSchemaAnalysis) -> None:
        """Print comprehensive analysis summary."""
        
        console.print("\n📊 PostgreSQL Base Schema Analysis", style="bold cyan")
        console.print("=" * 60)
        
        # Basic statistics
        stats_table = Table(title="Base Schema Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Hasura Endpoint", analysis.endpoint)
        stats_table.add_row("Base Tables Found", str(analysis.summary["total_base_tables"]))
        stats_table.add_row("Tables with Data", str(analysis.summary["tables_with_data"]))
        stats_table.add_row("Relationships Found", str(analysis.summary["total_relationships"]))
        
        if analysis.summary["total_estimated_rows"]:
            stats_table.add_row("Total Estimated Rows", f"{analysis.summary['total_estimated_rows']:,}")
        
        console.print(stats_table)
        
        # Largest tables by row count
        if analysis.summary["largest_tables"]:
            console.print("\n📈 Largest Base Tables", style="bold")
            largest_table = Table()
            largest_table.add_column("Table Name", style="cyan")
            largest_table.add_column("Estimated Rows", style="green", justify="right")
            
            for table_name, row_count in analysis.summary["largest_tables"]:
                if row_count:
                    largest_table.add_row(table_name, f"{row_count:,}")
            
            console.print(largest_table)
        
        # Most connected tables (by foreign keys)
        if analysis.summary["most_connected_tables"]:
            console.print("\n🔗 Most Connected Tables (by Foreign Keys)", style="bold")
            connected_table = Table()
            connected_table.add_column("Table Name", style="cyan")
            connected_table.add_column("Foreign Keys", style="yellow", justify="right")
            
            for table_name, fk_count in analysis.summary["most_connected_tables"]:
                connected_table.add_row(table_name, str(fk_count))
            
            console.print(connected_table)
        
        # All base tables with field counts
        console.print(f"\n📚 All Base Tables ({len(analysis.base_tables)}):", style="bold")
        all_tables = Table()
        all_tables.add_column("Table Name", style="cyan")
        all_tables.add_column("Fields", style="green", justify="right")
        all_tables.add_column("Foreign Keys", style="yellow", justify="right")
        all_tables.add_column("Estimated Rows", style="blue", justify="right")
        
        for table in sorted(analysis.base_tables, key=lambda t: t.name):
            fk_count = sum(1 for f in table.fields if f.is_foreign_key)
            row_display = f"{table.estimated_rows:,}" if table.estimated_rows else "-"
            
            all_tables.add_row(
                table.name,
                str(len(table.fields)),
                str(fk_count) if fk_count > 0 else "-",
                row_display
            )
        
        console.print(all_tables)
        
        # Key relationships
        if analysis.relationships:
            console.print(f"\n🔗 Discovered Relationships ({len(analysis.relationships)}):", style="bold")
            
            # Group relationships by type
            by_type = {}
            for rel in analysis.relationships:
                rel_type = rel["relationship_type"]
                if rel_type not in by_type:
                    by_type[rel_type] = []
                by_type[rel_type].append(rel)
            
            for rel_type, rels in by_type.items():
                console.print(f"\n  {rel_type}:", style="yellow")
                for rel in rels[:10]:  # Show first 10 of each type
                    console.print(f"    {rel['from_table']}.{rel['from_field']} → {rel['to_table']}.{rel['to_field']}")
                if len(rels) > 10:
                    console.print(f"    ... and {len(rels) - 10} more")

@click.command()
@click.option('--endpoint', help='Hasura GraphQL endpoint URL')
@click.option('--admin-secret', help='Hasura admin secret/token')
@click.option('--output', default='base-schema-analysis.json', help='Output file for analysis results')
def main(endpoint, admin_secret, output):
    """Discover actual PostgreSQL base table schema behind Hasura GraphQL."""
    
    # Use environment variables if not provided
    if not endpoint:
        endpoint = os.getenv('HASURA_ENDPOINT')
        if not endpoint:
            endpoint = click.prompt('Hasura GraphQL endpoint')
    
    if not admin_secret:
        admin_secret = os.getenv('HASURA_ADMIN_SECRET')
    
    try:
        # Initialize discoverer
        discoverer = BaseSchemaDiscoverer(endpoint, admin_secret)
        
        # Connect and analyze
        discoverer.connect()
        analysis = discoverer.discover_base_schema()
        
        # Save and display results
        discoverer.save_analysis(analysis, output)
        discoverer.print_analysis_summary(analysis)
        
        console.print(f"\n✅ Base schema discovery completed!", style="bold green")
        console.print(f"📄 Results saved to: {output}")
        console.print("\n💡 This shows the actual PostgreSQL tables (not computed views)")
        
    except Exception as e:
        console.print(f"❌ Discovery failed: {e}", style="bold red")
        raise

if __name__ == "__main__":
    main()