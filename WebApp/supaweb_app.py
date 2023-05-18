from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
from datetime import datetime
import pymysql
import json
import requests
from supabase import create_client

app = Flask(__name__)
CORS(app)

# Replace with your actual database configuration
config = {
    'host': 'agaidatabase.cog2fppyk9lm.us-east-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'measuremeinmeteredlines',
    'database': 'agaidatabase'
}

# Utility function to get a database connection
def get_db_connection():
    return pymysql.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )


@app.route('/write_serial', methods=['GET'])
def write_serial():
    username = request.args.get('username')
    serial_number = request.args.get('serial_number')

    if not username or not serial_number:
        return "Username or serial number is missing."

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM clients WHERE username = %s", (username,))
    result = cursor.fetchone()

    if result:
        # If the username exists, update the serials list
        serials = json.loads(result[2])
        if serial_number not in serials:
            serials.append(serial_number)
            cursor.execute("UPDATE clients SET serials = %s WHERE username = %s", (json.dumps(serials), username))
            connection.commit()
    else:
        # If the username doesn't exist, create a new entry
        cursor.execute("INSERT INTO clients (username, serials) VALUES (%s, %s)", (username, json.dumps([serial_number])))
        connection.commit()

    cursor.close()
    connection.close()
    response = Response("Serial number saved successfully.")
    response.headers.set('Content-Type', 'text/plain')
    return response


@app.route('/get_serials', methods=['GET'])
def get_serials():
    username = request.args.get('username')

    if not username:
        return "Username is missing."

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get the serial numbers for the given username
    cursor.execute("SELECT serials FROM clients WHERE username = %s", (username,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    if result:
        serials = json.loads(result[0])
        response_text = "\n".join(serials)
        if not response_text:
            response_text = "No serial numbers found for the given username."
    else:
        response_text = "Username not found."

    response = Response(response_text)
    response.headers.set('Content-Type', 'text/plain')
    return response


@app.route('/get_latest_data', methods=['GET'])
def get_latest_data():

    # Works like http://localhost:5000/get_latest_data?username=a1&serial_number=E1D281D3111E

    username = request.args.get('username')
    serial_number = request.args.get('serial_number')

    if not username or not serial_number:
        return "Username or serial number is missing."

    table_name = f"client_{username}"
    connection = get_db_connection()
    cursor = connection.cursor()

    # Get the most recent entry for the given username and serial number
    cursor.execute(f"SELECT * FROM {table_name} WHERE camera = %s ORDER BY date_stamp DESC LIMIT 1", (serial_number,))
    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        return "No data found for the specified username and serial number."

    date_stamp, cam_id, master_boxes_json = row[1], row[3], row[-2]
    dt = datetime.strptime(date_stamp, "%Y%m%d-%H%M%S")
    formatted_dt = dt.strftime("%B %d, %Y %I:%M %p")

    # master_boxes = json.loads(master_boxes_json)

    # response_text = f"datetime: {formatted_dt}\n"
    # for box in master_boxes:
    #     response_text += " ".join(str(x) for x in box) + "\n"

    # response = Response(response_text)
    # response.headers.set('Content-Type', 'text/plain')
    # return response

    img_path = f"mysite/static/{username}-{cam_id}-{date_stamp}.jpg"

    url = f"https://agaicamstorage.s3.us-west-2.amazonaws.com/images/{username}-{cam_id}-{date_stamp}.jpg"
    filename = f"{username}-{cam_id}-{date_stamp}.jpg"

    response = requests.get(url)

    if response.status_code == 200:
        with open(f'mysite/static/{filename}', 'wb') as file:
            file.write(response.content)
            img_path = f"static/{username}-{cam_id}-{date_stamp}.jpg"
    else:
        print(f"Error downloading file: {response.status_code}")

    master_boxes = json.loads(master_boxes_json)

    response_data = {
        "datetime": formatted_dt,
        "datestring": date_stamp,
        "imgurl": f"{request.url_root}{img_path}",
        "master_boxes": master_boxes
    }

    response_text = f"datetime: {formatted_dt}\n"
    response_text += f"datestring: {date_stamp}\n"
    response_text += f"imgurl: {request.url_root}{img_path}\n"

    for box in master_boxes:
        response_text += " ".join(str(x) for x in box) + "\n"

    response = make_response(response_text)
    response.headers.set('Content-Type', 'text/plain')
    return response

@app.route('/get_data_by_date', methods=['GET'])
def get_data_by_date():

    # Here is a query that works http://localhost:5000/get_data_by_date?username=a1&serial_number=E1D281D3111E&date=20230408

    username = request.args.get('username')
    serial_number = request.args.get('serial_number')
    date = request.args.get('date')

    if not username or not serial_number or not date:
        return "Username, serial number, or date is missing."

    table_name = f"client_{username}"
    connection = get_db_connection()
    cursor = connection.cursor()

    # Convert input date to datetime object and get the date part only
    # input_date = datetime.strptime(date, "%Y%m%d").date()
    input_date = datetime.strptime(date, "%Y%m%d").strftime("%Y%m%d")


    # Get all entries for the given username, serial number, and date
    # cursor.execute(f"SELECT * FROM {table_name} WHERE client_id = %s AND camera = %s AND date_stamp LIKE %s", (username, serial_number, f"{input_date}-%"))

    print(f"Executing query: SELECT * FROM {table_name} WHERE client_id = '{username}' AND camera = '{serial_number}' AND date_stamp LIKE '{input_date}-%'")
    cursor.execute(f"SELECT * FROM {table_name} WHERE client_id = %s AND camera = %s AND date_stamp LIKE %s", (username, serial_number, f"{input_date}-%"))
    # print(f"Rows fetched: {len(rows)}")

    rows = cursor.fetchall()
    print(f"Rows fetched: {len(rows)}")


    cursor.close()
    connection.close()

    if not rows:
        return "No data found for the specified username, serial number, and date."

    # response_text = ""
    # for row in rows:
    #     date_stamp, cam_id, master_boxes_json = row[1], row[3], row[-2]
    #     # Check if the date stamp starts with the input date
    #     if date_stamp.startswith(date):
    #         dt = datetime.strptime(date_stamp, "%Y%m%d-%H%M%S")
    #         formatted_dt = dt.strftime("%B %d, %Y %I:%M %p")

    #         master_boxes = json.loads(master_boxes_json)

    #         response_text += f"datetime: {formatted_dt}\n"
    #         for box in master_boxes:
    #             response_text += " ".join(str(x) for x in box) + "\n"

    #         response_text += "\n"

    response_text = ""
    for row in rows:
        date_stamp = row[1]
        # Check if the date stamp starts with the input date
        if date_stamp.startswith(date):
            response_text += f"{date_stamp}\n"


    response = Response(response_text)
    response.headers.set('Content-Type', 'text/plain')
    return response





@app.route('/get_data_by_timestamp', methods=['GET'])
def get_data_by_timestamp():

    # Example Connection: http://localhost:5000/get_data_by_timestamp?username=a1&serial_number=E1D281D3111E&date=20230408-203955

    username = request.args.get('username')
    serial_number = request.args.get('serial_number')
    date = request.args.get('date')  # <-- Change parameter name here

    if not username or not serial_number or not date:  # <-- Change parameter name here
        return "Username, serial number, or date is missing."  # <-- Change error message here

    table_name = f"client_{username}"
    connection = get_db_connection()
    cursor = connection.cursor()

    # Get the entry for the given username, serial number, and timestamp
    cursor.execute(f"SELECT * FROM {table_name} WHERE camera = %s AND date_stamp = %s", (serial_number, date))  # <-- Change parameter name here
    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        return "No data found for the specified username, serial number, and date."  # <-- Change error message here

    date_stamp, cam_id, master_boxes_json = row[1], row[3], row[-2]
    dt = datetime.strptime(date_stamp, "%Y%m%d-%H%M%S")
    formatted_dt = dt.strftime("%B %d, %Y %I:%M %p")

    master_boxes = json.loads(master_boxes_json)

    response_text = f"datetime: {formatted_dt}\n"
    for box in master_boxes:
        response_text += " ".join(str(x) for x in box) + "\n"

    response = Response(response_text)
    response.headers.set('Content-Type', 'text/plain')
    return response



@app.route('/get_previous_next', methods=['GET'])
def get_previous_next():

    # Works like http://localhost:5000/get_previous_next?username=a1&serial_number=E1D281D3111E&timestamp=20230408-203957&direction=previous

    username = request.args.get('username')
    serial_number = request.args.get('serial_number')
    timestamp = request.args.get('timestamp')
    direction = request.args.get('direction')

    if not username or not serial_number or not timestamp or not direction:
        return "Username, serial number, timestamp, or direction is missing."

    if direction not in ["previous", "next"]:
        return "Invalid direction value. It should be either 'previous' or 'next'."

    table_name = f"client_{username}"
    connection = get_db_connection()
    cursor = connection.cursor()

    # Convert input timestamp to datetime object
    input_timestamp = datetime.strptime(timestamp, "%Y%m%d-%H%M%S")

    if direction == "previous":
        order_by = "DESC"
        comparison_operator = "<"
    else:  # direction == "next"
        order_by = "ASC"
        comparison_operator = ">"

    # Get the previous or next entry for the given username, serial number, and timestamp
    cursor.execute(f"SELECT * FROM {table_name} WHERE camera = %s AND date_stamp {comparison_operator} %s ORDER BY date_stamp {order_by} LIMIT 1",
                   (serial_number, input_timestamp.strftime("%Y%m%d-%H%M%S")))
    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        return f"No {direction} data found for the specified username, serial number, and timestamp."

    date_stamp, cam_id, master_boxes_json = row[1], row[3], row[-2]
    dt = datetime.strptime(date_stamp, "%Y%m%d-%H%M%S")
    formatted_dt = dt.strftime("%B %d, %Y %I:%M %p")

    # master_boxes = json.loads(master_boxes_json)

    # response_text = f"datetime: {formatted_dt}\n"
    # for box in master_boxes:
    #     response_text += " ".join(str(x) for x in box) + "\n"

    # response = Response(response_text)
    # response.headers.set('Content-Type', 'text/plain')
    # return response

    img_path = f"mysite/static/{username}-{cam_id}-{date_stamp}.jpg"

    url = f"https://agaicamstorage.s3.us-west-2.amazonaws.com/images/{username}-{cam_id}-{date_stamp}.jpg"
    filename = f"{username}-{cam_id}-{date_stamp}.jpg"

    response = requests.get(url)

    if response.status_code == 200:
        with open(f'mysite/static/{filename}', 'wb') as file:
            file.write(response.content)
            img_path = f"static/{username}-{cam_id}-{date_stamp}.jpg"
    else:
        print(f"Error downloading file: {response.status_code}")

    master_boxes = json.loads(master_boxes_json)

    response_data = {
        "datetime": formatted_dt,
        "datestring": date_stamp,
        "imgurl": f"{request.url_root}{img_path}",
        "master_boxes": master_boxes
    }

    response_text = f"datetime: {formatted_dt}\n"
    response_text += f"datestring: {date_stamp}\n"
    response_text += f"imgurl: {request.url_root}{img_path}\n"

    for box in master_boxes:
        response_text += " ".join(str(x) for x in box) + "\n"

    response = make_response(response_text)
    response.headers.set('Content-Type', 'text/plain')
    return response


@app.route('/create_client_table', methods=['GET'])
def create_client_table():
    # Implement the logic to create a table with a list of client ids/usernames and serials
    pass


if __name__ == '__main__':
    app.run()