import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect(r'd:\Projects\PortfolioAI\portfolio-backend\test.db')

# Create a cursor object
cursor = conn.cursor()

# Drop the alembic_version table if it exists
cursor.execute("DROP TABLE IF EXISTS alembic_version;")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Alembic version table removed successfully.")
