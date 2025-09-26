#!/usr/bin/env python3

"""
Database utility functions for Oak Knowledge Graph pipeline.
Provides database management operations like clearing, stats, and health checks.
"""

import sys
import os
from typing import Dict, Any, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.auradb_loader import AuraDBLoader


def clear_database_interactive() -> bool:
    """
    Interactive database cleanup tool with confirmation prompts.

    Returns:
        bool: True if database was cleared successfully, False otherwise
    """
    print("🗑️  AuraDB Database Cleanup Tool")
    print("=" * 40)

    try:
        loader = AuraDBLoader()
        print("✅ Connected to AuraDB")

        # Get current stats
        stats = loader.get_database_stats()
        if "error" in stats:
            print(f"❌ Error getting database stats: {stats['error']}")
            return False

        print(f"\nCurrent database contents:")
        print(f"   Nodes: {stats['nodes']}")
        print(f"   Relationships: {stats['relationships']}")
        print(f"   Node labels: {stats['node_labels']}")
        print(f"   Relationship types: {stats['relationship_types']}")

        if stats["nodes"] == 0:
            print("\n✅ Database is already empty!")
            return True

        # Confirm deletion
        confirm = input(
            f"\n⚠️  This will DELETE ALL {stats['nodes']} nodes and {stats['relationships']} relationships!\n   Continue? (type 'DELETE' to confirm): "
        )

        if confirm != "DELETE":
            print("❌ Deletion cancelled")
            return False

        # Clear database
        print("\n🗑️  Clearing database...")
        success, message = loader.clear_database()

        if success:
            print(f"✅ {message}")
            print("🎉 Database cleared successfully!")
            return True
        else:
            print(f"❌ {message}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def get_database_stats() -> Dict[str, Any]:
    """
    Get database statistics without prompts.

    Returns:
        dict: Database statistics including node count, relationships, labels, etc.
    """
    try:
        loader = AuraDBLoader()
        return loader.get_database_stats()
    except Exception as e:
        return {"error": f"Failed to get database stats: {str(e)}"}


def clear_database_silent(confirm: bool = False) -> Tuple[bool, str]:
    """
    Clear database without interactive prompts.

    Args:
        confirm: Must be True to actually clear the database (safety check)

    Returns:
        tuple: (success: bool, message: str)
    """
    if not confirm:
        return False, "Confirmation required: call with confirm=True"

    try:
        loader = AuraDBLoader()
        return loader.clear_database()
    except Exception as e:
        return False, f"Failed to clear database: {str(e)}"


def test_database_connection() -> Tuple[bool, str]:
    """
    Test database connection without making changes.

    Returns:
        tuple: (connected: bool, message: str)
    """
    try:
        loader = AuraDBLoader()
        return loader.test_connection()
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"


if __name__ == "__main__":
    """Run interactive database cleanup when script is executed directly"""
    success = clear_database_interactive()
    sys.exit(0 if success else 1)
