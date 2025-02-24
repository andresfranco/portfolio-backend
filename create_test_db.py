import sqlite3

# Connect to the SQLite database (create the file if it does not exist)
conn = sqlite3.connect(r'd:\Projects\PortfolioAI\portfolio-backend\test.db')

# Close the connection
conn.close()

print("SQLite database file created successfully.")
