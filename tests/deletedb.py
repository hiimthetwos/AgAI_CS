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

    # Delete the 'client_a1' table
    cursor = conn.cursor()
    cursor.execute('DROP TABLE client_a1')
    print('Deleted the client_a1 table')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

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
