import psycopg
from config.settings import DATABASE_URL
from mcp.server.fastmcp import FastMCP

# initialize database mcp server
mcp = FastMCP("database-server")

# mcp tool: lookup customer record by customer id
@mcp.tool()
def lookup_customer(customer_id: int) -> dict:
    """Look up a customer by their ID."""
    # validate database connection string configuration
    if not DATABASE_URL:
        return {"error": "DATABASE_URL is not set in environment."}

    try:
        # connect to database and execute query
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # execute parameterized select query
                cur.execute(
                    """
                    SELECT id, name, email, company, status
                    FROM customers
                    WHERE id = %s
                    """,
                    (customer_id,),
                )
                row = cur.fetchone()

    except psycopg.Error as err:
        # return safe error response on database failure
        return {"error": f"Database error: {err}"}

    # return error if no customer found
    if row is None:
        return {"error": "Customer not found"}

    # return customer details dictionary
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "company": row[3],
        "status": row[4],
    }

# run server directly if executed
if __name__ == "__main__":
    mcp.run()