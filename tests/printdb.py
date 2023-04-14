import pymysql

# Define connection details
connection = pymysql.connect(
    host='agaidatabase.cog2fppyk9lm.us-east-2.rds.amazonaws.com',
    user='admin',
    password='measuremeinmeteredlines',
    database='agaidatabase'
)

# Create a cursor object
cursor = connection.cursor()

# Get all table names
cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()

# Loop through tables and print entries
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    print(f"{table_name}:")
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    print(columns)
    for row in rows:
        print(row)

# Close cursor and connection
cursor.close()
connection.close()