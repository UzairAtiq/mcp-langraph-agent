import os
import psycopg
from config import DATABASE_URL
from mcp.server.mcpserver import MCPServer

#Creating the mcp server 
mcp = MCPServer("database-server")

#defining the mcp tool for getting customer
@mcp.tool()
def lookup_customer(customer_id: int) -> dict:
    """Look up a customer by their ID."""
    with psycopg.connect(DATABASE_URL) as conn:

        #creating cursor for python to execute querie
        with conn.cursor() as cur:

            #executing the query
            cur.execute(
                """
                SELECT id, name, email, company, status
                FROM customers
                WHERE id = %s
                """,
                (customer_id,),
            )

            row = cur.fetchone()
    #reutrn error if no customer with the id is found
    if row is None:
        return {"error": "Customer not found"}

    #if customer with id found then reutrn their details 
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "company": row[3],
        "status": row[4],
    }


print(lookup_customer(3))