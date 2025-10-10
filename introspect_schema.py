#!/usr/bin/env python3
"""
Neo4j Schema Introspection Script
Analyzes the UK Curriculum Knowledge Graph schema
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


class SchemaIntrospector:
    def __init__(self, uri, username, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database

    def close(self):
        self.driver.close()

    def run_query(self, query, description):
        """Execute a query and return results"""
        print(f"\n{'=' * 80}")
        print(f"QUERY: {description}")
        print(f"{'=' * 80}")
        print(f"{query}\n")

        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            records = [record.data() for record in result]
            print(f"Results ({len(records)} records):")
            print(json.dumps(records, indent=2, default=str))
            return records

    def get_node_labels_and_counts(self):
        """Get all node labels and their counts"""
        query = """
        CALL db.labels() YIELD label
        CALL {
            WITH label
            MATCH (n) WHERE label IN labels(n)
            RETURN count(n) as count
        }
        RETURN label, count
        ORDER BY label
        """
        return self.run_query(query, "Node Labels and Counts")

    def get_relationship_types_and_counts(self):
        """Get all relationship types and their counts"""
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        CALL {
            WITH relationshipType
            MATCH ()-[r]->() WHERE type(r) = relationshipType
            RETURN count(r) as count
        }
        RETURN relationshipType, count
        ORDER BY relationshipType
        """
        return self.run_query(query, "Relationship Types and Counts")

    def get_sample_nodes_for_label(self, label):
        """Get sample nodes for a specific label"""
        query = f"""
        MATCH (n:`{label}`)
        RETURN n
        LIMIT 3
        """
        return self.run_query(query, f"Sample Nodes for Label: {label}")

    def get_all_sample_nodes(self):
        """Get sample nodes for all labels"""
        labels_result = self.get_node_labels_and_counts()
        all_samples = {}
        for record in labels_result:
            label = record["label"]
            samples = self.get_sample_nodes_for_label(label)
            all_samples[label] = samples
        return all_samples

    def get_relationship_patterns(self):
        """Get all relationship patterns with counts"""
        query = """
        MATCH (a)-[r]->(b)
        WITH labels(a)[0] as from, type(r) as rel, labels(b)[0] as to, count(*) as count
        RETURN from, rel, to, count
        ORDER BY count DESC
        """
        return self.run_query(query, "Relationship Patterns")

    def get_properties_by_label(self, label):
        """Get all properties and their types for a label"""
        query = f"""
        MATCH (n:`{label}`)
        WITH n LIMIT 100
        UNWIND keys(n) as key
        WITH key, n[key] as value
        RETURN DISTINCT key,
               apoc.meta.cypher.type(value) as type,
               collect(DISTINCT value)[0..3] as sampleValues
        ORDER BY key
        """
        return self.run_query(query, f"Properties for Label: {label}")

    def get_all_properties(self):
        """Get properties for all labels"""
        labels_result = self.get_node_labels_and_counts()
        all_properties = {}
        for record in labels_result:
            label = record["label"]
            try:
                properties = self.get_properties_by_label(label)
                all_properties[label] = properties
            except Exception as e:
                print(f"Warning: Could not get properties for {label}: {e}")
                # Try without APOC if it's not available
                query = f"""
                MATCH (n:`{label}`)
                WITH n LIMIT 100
                UNWIND keys(n) as key
                RETURN DISTINCT key
                ORDER BY key
                """
                properties = self.run_query(
                    query, f"Properties for Label: {label} (no APOC)"
                )
                all_properties[label] = properties
        return all_properties

    def run_full_introspection(self):
        """Run complete schema introspection"""
        print("\n" + "=" * 80)
        print("NEO4J SCHEMA INTROSPECTION")
        print("=" * 80)

        # 1. Node labels and counts
        self.get_node_labels_and_counts()

        # 2. Relationship types and counts
        self.get_relationship_types_and_counts()

        # 3. Relationship patterns
        self.get_relationship_patterns()

        # 4. Sample nodes for each label
        print("\n" + "=" * 80)
        print("SAMPLE NODES")
        print("=" * 80)
        self.get_all_sample_nodes()

        # 5. Properties for each label
        print("\n" + "=" * 80)
        print("PROPERTIES BY LABEL")
        print("=" * 80)
        self.get_all_properties()

        print("\n" + "=" * 80)
        print("INTROSPECTION COMPLETE")
        print("=" * 80)


def main():
    """Main execution"""
    introspector = SchemaIntrospector(
        NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE
    )
    try:
        introspector.run_full_introspection()
    finally:
        introspector.close()


if __name__ == "__main__":
    main()
