import pymysql

config = {
    'host': 'agaidatabase.cog2fppyk9lm.us-east-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'measuremeinmeteredlines',
    'database': 'agaidatabase'
}

# Connect to the MySQL server
print("Connecting to database...")
try:
    conn = pymysql.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    print("Connection established")
except pymysql.err.OperationalError as err:
    if err.args[0] == 1045:  # Access denied error
        print("Something is wrong with the user name or password")
    elif err.args[0] == 1049:  # Unknown database error
        # Create the database if it does not exist
        conn = pymysql.connect(
            host=config['host'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE {}".format(config['database']))
        print("Database created")
        conn.close()
        # Reconnect to the newly created database
        conn = pymysql.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
    else:
        print(err)

cursor = conn.cursor()

cursor.execute(f"USE {config['database']}")

# Query the information_schema database to retrieve the size of every table in the database
cursor.execute("SELECT table_name, (data_length + index_length) / 1024 / 1024 AS size_mb FROM information_schema.tables WHERE table_schema = %s", (config['database'],))

# Print the results
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]:.2f} MB")

# Clean up
cursor.close()
conn.close()
