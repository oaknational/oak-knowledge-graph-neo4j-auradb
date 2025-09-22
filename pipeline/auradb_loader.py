import os
import pandas as pd
from typing import Dict, List, Tuple, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv


class AuraDBLoader:
    def __init__(self, clear_before_import: bool = False):
        load_dotenv()
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.clear_before_import = clear_before_import

        if not all([self.uri, self.username, self.password]):
            raise ValueError(
                "Missing Neo4j connection details. Please set NEO4J_URI, "
                "NEO4J_USERNAME, and NEO4J_PASSWORD environment variables."
            )

    def test_connection(self) -> Tuple[bool, str]:
        try:
            # Simple connection pattern matching working script
            driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                driver.close()
                return True, f"Connection successful! Test returned: {test_value}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def generate_batch_queries(
        self, node_files: List[str], relationship_files: List[str], batch_size: int = 1000
    ) -> List[Tuple[str, Dict]]:
        """Generate UNWIND batch queries for high-performance import"""
        queries = []

        # Generate node import queries
        for node_file in node_files:
            if os.path.exists(node_file):
                batch_queries = self._generate_node_batch_queries(node_file, batch_size)
                queries.extend(batch_queries)

        # Generate relationship import queries
        for rel_file in relationship_files:
            if os.path.exists(rel_file):
                batch_queries = self._generate_relationship_batch_queries(rel_file, batch_size)
                queries.extend(batch_queries)

        return queries

    def _generate_node_load_query(self, csv_file: str) -> str:
        # Read CSV headers to build dynamic query
        df = pd.read_csv(csv_file, nrows=0)

        # Extract label from filename or use default
        filename = os.path.basename(csv_file)
        if "_nodes.csv" in filename:
            label = filename.replace("_nodes.csv", "").title()
        else:
            label = "Node"

        # Build property assignments (remove type annotations for Cypher)
        properties = []
        for col in df.columns:
            if col == ":ID":
                continue  # Skip ID column
            elif col == ":LABEL":
                continue  # Skip label column, use dynamic label
            elif ":" in col:
                prop_name = col.split(":")[0]
                properties.append(f"{prop_name}: row.`{col}`")
            else:
                properties.append(f"{col}: row.`{col}`")

        property_string = ", ".join(properties) if properties else ""

        query = f"""
LOAD CSV WITH HEADERS FROM 'file:///{csv_file}' AS row
CREATE (n:{label} {{id: row.`:ID`{', ' + property_string if property_string else ''}}})
"""
        return query.strip()

    def _generate_relationship_load_query(self, csv_file: str) -> str:
        # Read CSV to get headers and relationship type
        df_sample = pd.read_csv(csv_file, nrows=1)  # Read one row to get :TYPE value
        df_headers = pd.read_csv(csv_file, nrows=0)  # Get just headers for column info

        # Extract relationship type from :TYPE column in CSV (not filename)
        if ":TYPE" in df_sample.columns and not df_sample.empty:
            rel_type = df_sample[":TYPE"].iloc[0]  # Get the relationship type from the first row
        else:
            # Fallback to filename if :TYPE column is missing
            filename = os.path.basename(csv_file)
            if "_relationships.csv" in filename:
                rel_type = filename.replace("_relationships.csv", "").upper()
            else:
                rel_type = "RELATED_TO"

        # Build property assignments (remove type annotations for Cypher)
        properties = []
        for col in df_headers.columns:
            if col in [":START_ID", ":END_ID", ":TYPE"]:
                continue  # Skip special columns
            elif ":" in col:
                prop_name = col.split(":")[0]
                properties.append(f"{prop_name}: row.`{col}`")
            else:
                properties.append(f"{col}: row.`{col}`")

        property_string = ", ".join(properties) if properties else ""

        query = f"""
LOAD CSV WITH HEADERS FROM 'file:///{csv_file}' AS row
MATCH (start {{id: row.`:START_ID`}})
MATCH (end {{id: row.`:END_ID`}})
CREATE (start)-[r:{rel_type}{{{property_string}}}]->(end)
"""
        return query.strip()

    def _generate_node_batch_queries(self, csv_file: str, batch_size: int) -> List[Tuple[str, Dict]]:
        """Generate UNWIND batch queries for high-performance node import"""
        df = pd.read_csv(csv_file)

        # Extract label from filename
        filename = os.path.basename(csv_file)
        if "_nodes.csv" in filename:
            label = filename.replace("_nodes.csv", "").replace("sample_", "").title()
        else:
            label = "Node"

        # Build property mapping for query template
        property_assignments = ["id: row.id"]

        for col in df.columns:
            if col in [":ID", ":LABEL"]:
                continue
            elif ":" in col:
                prop_name = col.split(":")[0]
                property_assignments.append(f"{prop_name}: row.{prop_name}")
            else:
                property_assignments.append(f"{col}: row.{col}")

        # Create UNWIND query template
        prop_string = ", ".join(property_assignments)
        query_template = f"""
UNWIND $batch AS row
CREATE (n:{label} {{{prop_string}}})
""".strip()

        # Process data in batches
        queries = []
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i + batch_size]

            # Convert batch to list of dicts with proper types
            batch_data = []
            for _, row in batch_df.iterrows():
                record = {"id": row[":ID"]}

                for col in df.columns:
                    if col in [":ID", ":LABEL"]:
                        continue
                    elif ":" in col:
                        prop_name = col.split(":")[0]
                        value = row[col]
                        if not pd.isna(value):
                            # Convert based on type annotation
                            if "int" in col:
                                record[prop_name] = int(value)
                            elif "float" in col:
                                record[prop_name] = float(value)
                            elif "boolean" in col:
                                record[prop_name] = bool(value)
                            else:
                                record[prop_name] = str(value)
                    else:
                        value = row[col]
                        if not pd.isna(value):
                            record[col] = str(value)

                batch_data.append(record)

            # Add query with parameters
            queries.append((query_template, {"batch": batch_data}))

        return queries

    def _generate_relationship_batch_queries(self, csv_file: str, batch_size: int) -> List[Tuple[str, Dict]]:
        """Generate UNWIND batch queries for high-performance relationship import"""
        df = pd.read_csv(csv_file)

        # Extract relationship type from :TYPE column in CSV (not filename)
        if ":TYPE" in df.columns and not df.empty:
            rel_type = df[":TYPE"].iloc[0]  # Get the relationship type from the first row
        else:
            # Fallback to filename if :TYPE column is missing
            filename = os.path.basename(csv_file)
            if "_relationships.csv" in filename:
                rel_type = filename.replace("_relationships.csv", "").replace("sample_", "").upper()
            else:
                rel_type = "RELATED_TO"

        # Build property mapping for query template
        property_assignments = []
        for col in df.columns:
            if col in [":START_ID", ":END_ID", ":TYPE"]:
                continue
            elif ":" in col:
                prop_name = col.split(":")[0]
                property_assignments.append(f"{prop_name}: row.{prop_name}")
            else:
                property_assignments.append(f"{col}: row.{col}")

        # Create UNWIND query template
        prop_string = "{" + ", ".join(property_assignments) + "}" if property_assignments else ""
        query_template = f"""
UNWIND $batch AS row
MATCH (start {{id: row.start_id}})
MATCH (end {{id: row.end_id}})
CREATE (start)-[r:{rel_type}{prop_string}]->(end)
""".strip()

        # Process data in batches
        queries = []
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i + batch_size]

            # Convert batch to list of dicts with proper types
            batch_data = []
            for _, row in batch_df.iterrows():
                record = {
                    "start_id": row[":START_ID"],
                    "end_id": row[":END_ID"]
                }

                for col in df.columns:
                    if col in [":START_ID", ":END_ID", ":TYPE"]:
                        continue
                    elif ":" in col:
                        prop_name = col.split(":")[0]
                        value = row[col]
                        if not pd.isna(value):
                            # Convert based on type annotation
                            if "int" in col:
                                record[prop_name] = int(value)
                            elif "float" in col:
                                record[prop_name] = float(value)
                            elif "boolean" in col:
                                record[prop_name] = bool(value)
                            else:
                                record[prop_name] = str(value)
                    else:
                        value = row[col]
                        if not pd.isna(value):
                            record[col] = str(value)

                batch_data.append(record)

            # Add query with parameters
            queries.append((query_template, {"batch": batch_data}))

        return queries

    def execute_import(
        self, node_files: List[str], relationship_files: List[str]
    ) -> Dict[str, any]:
        results = {
            "success": False,
            "queries_executed": 0,
            "total_queries": 0,
            "errors": [],
            "execution_summary": [],
            "database_cleared": False,
        }

        # Clear database if configured to do so
        if self.clear_before_import:
            clear_success, clear_message = self.clear_database()
            results["database_cleared"] = clear_success
            if not clear_success:
                results["errors"].append(f"Failed to clear database: {clear_message}")
                return results

        # Generate batch queries (UNWIND for high performance)
        batch_size = 1000  # Optimal batch size for performance
        queries = self.generate_batch_queries(node_files, relationship_files, batch_size)
        results["total_queries"] = len(queries)

        if not queries:
            results["errors"].append("No valid CSV files found for import")
            return results

        # Execute queries - exact working pattern (NO database specified in session)
        try:
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

            for i, (query, parameters) in enumerate(queries):
                try:
                    # CRITICAL: Don't specify database in session - like working script
                    with driver.session() as session:
                        result = session.run(query, parameters)
                        summary = result.consume()

                        execution_info = {
                            "query_index": i + 1,
                            "nodes_created": summary.counters.nodes_created,
                            "relationships_created": summary.counters.relationships_created,
                            "properties_set": summary.counters.properties_set,
                            "batch_size": len(parameters.get("batch", [])),
                            "query": (
                                query[:100] + "..." if len(query) > 100 else query
                            ),
                        }
                        results["execution_summary"].append(execution_info)
                        results["queries_executed"] += 1

                except Exception as e:
                    error_msg = f"Batch {i + 1} failed: {str(e)}"
                    results["errors"].append(error_msg)

            driver.close()
            results["success"] = (
                results["queries_executed"] == results["total_queries"]
            )

        except Exception as e:
            results["errors"].append(f"Database connection failed: {str(e)}")

        return results

    def clear_database(self) -> Tuple[bool, str]:
        """Clear all nodes and relationships - USE WITH CAUTION!"""
        try:
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with driver.session() as session:
                # Delete all relationships first
                result = session.run("MATCH ()-[r]-() DELETE r")
                rel_summary = result.consume()

                # Then delete all nodes
                result = session.run("MATCH (n) DELETE n")
                node_summary = result.consume()

                message = (
                    f"Cleared database: {rel_summary.counters.relationships_deleted} "
                    f"relationships, {node_summary.counters.nodes_deleted} nodes deleted"
                )
                driver.close()
                return True, message

        except Exception as e:
            return False, f"Failed to clear database: {str(e)}"

    def get_database_stats(self) -> Dict[str, any]:
        """Get current database statistics"""
        try:
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with driver.session() as session:
                # Count nodes
                node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = node_result.single()["node_count"]

                # Count relationships (directed to avoid double counting)
                rel_result = session.run(
                    "MATCH ()-[r]->() RETURN count(r) as rel_count"
                )
                rel_count = rel_result.single()["rel_count"]

                # Get node labels
                labels_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]

                # Get relationship types
                types_result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in types_result]

                driver.close()
                return {
                    "nodes": node_count,
                    "relationships": rel_count,
                    "node_labels": labels,
                    "relationship_types": rel_types,
                    "database": self.database,
                }

        except Exception as e:
            return {"error": f"Failed to get database stats: {str(e)}"}
