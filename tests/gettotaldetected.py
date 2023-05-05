import pymysql
import pymysql.cursors

# Connect to the database
config = {
    'host': 'beartooth',
    'user': 'root',
    'password': 'measuremeinmeteredlines',
    'database': 'agaidatabase'
}

connection = pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)

# Get the values from the 'number_detected' column and sum them up
table_name = 'client_a1'  # Replace with your table name
total_number_detected = 0

try:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT number_detected FROM {table_name}")
        result = cursor.fetchall()
        total_number_detected = sum(row['number_detected'] for row in result)
finally:
    connection.close()

print(f"Total number detected: {total_number_detected}")
