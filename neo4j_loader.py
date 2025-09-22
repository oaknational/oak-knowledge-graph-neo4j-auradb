import os
import logging
from typing import Dict, List, Any
from neo4j import GraphDatabase


class Neo4jLoader:
    """
    Simple Neo4j loader based on the working AuraDB implementation.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Neo4j connection details from environment (same as working version)
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not all([self.uri, self.username, self.password]):
            raise ValueError(
                "Missing Neo4j connection details. Please set NEO4J_URI, "
                "NEO4J_USERNAME, and NEO4J_PASSWORD environment variables."
            )

        self.logger.info(f"Neo4j connection - URI: {self.uri}, Username: {self.username}")

    def test_connection(self) -> bool:
        """Test connection using the same approach as working AuraDB loader."""
        try:
            driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                driver.close()
                self.logger.info(f"Connection successful! Test returned: {test_value}")
                return True
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False

    def import_data(self, mapped_data: Dict[str, Any], clear_database: bool = False) -> Dict[str, int]:
        """
        Import mapped data into Neo4j knowledge graph using working connection pattern.
        """
        self.logger.info("Starting Neo4j data import")

        # Test connection first
        if not self.test_connection():
            raise RuntimeError("Failed to connect to Neo4j")

        try:
            # Use the same connection pattern as working AuraDB loader
            driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )

            stats = {"nodes_created": 0, "relationships_created": 0}

            with driver.session() as session:
                # Clear database if requested
                if clear_database:
                    self.logger.info("Clearing existing database...")
                    session.run("MATCH (n) DETACH DELETE n")
                    self.logger.info("Database cleared")

                # Import nodes
                if "nodes" in mapped_data:
                    stats["nodes_created"] = self._import_nodes(session, mapped_data["nodes"])

                # Import relationships
                if "relationships" in mapped_data:
                    stats["relationships_created"] = self._import_relationships(
                        session, mapped_data["relationships"]
                    )

            driver.close()
            self.logger.info(f"Import completed: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Neo4j import failed: {e}")
            raise

    def _import_nodes(self, session, nodes_data: Dict[str, List[Dict[str, Any]]]) -> int:
        """Import nodes into Neo4j using UNWIND batch queries."""
        total_created = 0

        for node_label, nodes in nodes_data.items():
            self.logger.info(f"Importing {len(nodes)} nodes with label {node_label}")

            if not nodes:
                continue

            # Batch import nodes for performance (same as working implementation)
            batch_size = 1000
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i + batch_size]

                # Create Cypher query for batch import
                query = f"""
                UNWIND $nodes AS node
                CREATE (n:{node_label})
                SET n = node
                """

                result = session.run(query, nodes=batch)
                created = result.consume().counters.nodes_created
                total_created += created

                self.logger.debug(f"Created {created} {node_label} nodes in batch {i//batch_size + 1}")

            self.logger.info(f"Completed import of {node_label}: {len(nodes)} nodes")

        return total_created

    def _import_relationships(self, session, relationships_data: Dict[str, List[Dict[str, Any]]]) -> int:
        """Import relationships into Neo4j using UNWIND batch queries."""
        total_created = 0

        for rel_type, relationships in relationships_data.items():
            self.logger.info(f"Importing {len(relationships)} relationships of type {rel_type}")

            if not relationships:
                continue

            # Batch import relationships for performance
            batch_size = 1000
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i:i + batch_size]

                # Create Cypher query for batch relationship import
                query = f"""
                UNWIND $relationships AS rel
                MATCH (start_node {{id: rel.start_node_id}})
                MATCH (end_node {{id: rel.end_node_id}})
                CREATE (start_node)-[r:{rel_type}]->(end_node)
                """

                # Add properties if any (excluding the ID fields)
                if batch and any(key not in ['start_node_id', 'end_node_id', 'type'] for key in batch[0].keys()):
                    query += """
                    SET r += apoc.map.removeKeys(rel, ['start_node_id', 'end_node_id', 'type'])
                    """

                result = session.run(query, relationships=batch)
                created = result.consume().counters.relationships_created
                total_created += created

                self.logger.debug(f"Created {created} {rel_type} relationships in batch {i//batch_size + 1}")

            self.logger.info(f"Completed import of {rel_type}: {len(relationships)} relationships")

        return total_created