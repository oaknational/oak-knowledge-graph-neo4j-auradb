# Knowledge Graph Data Ingest Pipeline - Simplified

1. Access Hasura to retrieve data via specified Materialized Views
2. Join all MV data into single consolidated CSV
3. Optional data cleaning/preprocessing step
4. Map CSV fields to Neo4j knowledge graph schema via JSON configuration
5. Import directly into Neo4j knowledge graph

Simple batch job execution with JSON-based schema mapping for easy maintenance.


### Here are notes about bulk imports to Neo4j:

Why Do You Need IDs in Bulk Import?
Neo4j assigns internal IDs to nodes and relationships automatically, but these internal IDs are not stable or available during bulk import. The importer needs user-provided IDs in the CSVs so that it can connect relationships to nodes. After the import, you can remove these IDs if you don’t need them.
Key points:
• Internal IDs are unstable and should not be used as business keys.
• During bulk import, relationships must reference nodes by a provided :ID column.
• IDs can be throwaway values, only used to wire relationships.
• After import, you can delete the ID property if you don’t want it in the graph.
Node CSV Format
Example nodes.csv:
id:ID,name:string,age:int,:LABEL
1,Alice,33,Person
2,Bob,42,Person
3,Acme Corp,,Company
Relationship CSV Format
Example relationships.csv:
:START_ID,:END_ID,:TYPE,since:int
1,2,FRIEND,2018
1,3,WORKS_AT,2020
Property Types
Neo4j supports property typing in the header: string, int, float, boolean, arrays.
Example:
id:ID,tags:string[],score:float,:LABEL
1,"music;travel",9.5,Person
Running the Import
Command:
neo4j-admin database import full \
  --nodes=import/nodes.csv \
  --relationships=import/relationships.csv \
  neo4j
Performance Tips
• Split large files into smaller CSVs for parallel processing.
• Use numeric IDs for speed.
• Sort data by ID before import.
• Increase memory settings for better performance.
• Keep properties minimal during import, enrich later.
Using Throwaway IDs
If you don’t need IDs in your final graph, you can still assign simple throwaway IDs during import. They serve only to connect relationships.
End-to-End Example Workflow
1. persons.csv
id:ID,name:string,:LABEL
1,Alice,Person
2,Bob,Person
3,Charlie,Person
2. friendships.csv
:START_ID,:END_ID,:TYPE
1,2,FRIEND
2,3,FRIEND
3. Run bulk import
neo4j-admin database import full \
  --nodes=import/persons.csv \
  --relationships=import/friendships.csv \
  neo4j
4. Cleanup after import
MATCH (n:Person) REMOVE n.id;
After cleanup, only the 'name' property remains, and IDs are gone.



For Neo4j bulk imports, you don't necessarily need separate CSVs for every node type, but it's often the recommended approach for better organization and performance.
For Nodes:
Best practice: Use separate CSV files for each node label/type (e.g., users.csv, products.csv, orders.csv)
Alternative: You can combine multiple node types in one CSV, but you'll need to include a column to specify the label for each row
Benefits of separate files: Cleaner data structure, easier to manage different properties per node type, better performance during import
For Relationships:
Separate CSV files: Each relationship type should typically be in its own CSV file (e.g., user_bought_product.csv, user_follows_user.csv)
Required columns: At minimum, you need start node identifier, end node identifier, and relationship type
Node references: Use the same identifier values that you used in your node CSV files (often an ID or unique property)
Basic structure example:
nodes/
├── users.csv (userId, name, email, ...)
├── products.csv (productId, title, price, ...)
└── orders.csv (orderId, date, total, ...)

relationships/
├── user_placed_order.csv (userId, orderId)
├── order_contains_product.csv (orderId, productId, quantity)
└── user_reviewed_product.csv (userId, productId, rating, review)
Tools:
neo4j-admin database import (for initial database creation)
LOAD CSV Cypher command (for importing into existing database)
Neo4j Browser or Neo4j Desktop for smaller datasets
The separate file approach makes your import scripts cleaner and allows you to handle different node types with their specific properties more efficiently.
Retry
MH
neo4j-admin database import (for initial database creation)
How do I use this when I have multiple csvs for nodes and relationships?
Edit
The neo4j-admin database import command handles multiple CSV files elegantly. Here's how to structure it:
Basic Syntax
bash
neo4j-admin database import full \
    --nodes=Label1=path/to/nodes1.csv \
    --nodes=Label2=path/to/nodes2.csv \
    --relationships=REL_TYPE=path/to/relationships1.csv \
    --relationships=REL_TYPE2=path/to/relationships2.csv \
    neo4j
Complete Example
bash
neo4j-admin database import full \
    --nodes=User=import/users.csv \
    --nodes=Product=import/products.csv \
    --nodes=Order=import/orders.csv \
    --relationships=PLACED=import/user_placed_order.csv \
    --relationships=CONTAINS=import/order_contains_product.csv \
    --relationships=REVIEWED=import/user_reviewed_product.csv \
    --delimiter="," \
    --quote-character="\"" \
    --multiline-fields=true \
    neo4j
CSV File Requirements
Node CSV headers:
csv
userId:ID,name,email:string,age:int
1,John Doe,john@example.com,30
2,Jane Smith,jane@example.com,25
Relationship CSV headers:
csv
:START_ID,:END_ID,orderDate:datetime,total:float
1,101,2023-01-15T10:30:00,99.99
2,102,2023-01-16T14:20:00,149.50
Key Points:
:ID - Unique identifier for nodes (must match in relationship files)
:START_ID and :END_ID - Reference the node IDs for relationships
:LABEL - Optional way to specify multiple labels per node
Data types - Specify with :int, :float, :datetime, :boolean, etc.
Multiple Labels Example:
bash
--nodes=User:Person=import/users.csv \
--nodes=Product:Item=import/products.csv
Important Notes:
Database must be stopped before running this command
This creates a new database (destroys existing data)
All CSV files should be in the Neo4j import directory or use full paths
The final argument (neo4j) is the database name
This approach is much faster than LOAD CSV for large datasets since it bypasses the transaction log and builds the database files directly.

