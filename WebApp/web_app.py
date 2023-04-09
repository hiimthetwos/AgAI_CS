from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
import json
import os
from datetime import datetime
import base64
import requests

app = Flask(__name__)
CORS(app)

config = {
        'host': 'agaidatabase.cog2fppyk9lm.us-east-2.rds.amazonaws.com',
        'user': 'admin',
        'password': 'password',
        'database': 'agaidatabase'
}

@app.route('/<client_id>')
def latest_data(client_id):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        table_name = f"client_{client_id}"
        print(f"Using table {table_name}...")
        cursor.execute(f"USE {config['database']}")
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()

        if row is None:
            return "No data found for the specified client ID."

        print(row)

        date_stamp, cam_id, master_boxes_json = row[1], row[3], row[-2]
        dt = datetime.strptime(date_stamp, "%Y%m%d-%H%M%S")
        formatted_dt = dt.strftime("%B %d, %Y %I:%M %p")


        img_path = f"mysite/static/{client_id}-{cam_id}-{date_stamp}.jpg"

        url = f"https://agaicamstorage.s3.us-west-2.amazonaws.com/images/{client_id}-{cam_id}-{date_stamp}.jpg"
        filename = f"{client_id}-{cam_id}-{date_stamp}.jpg"

        response = requests.get(url)

        if response.status_code == 200:
            with open(f'mysite/static/{filename}', 'wb') as file:
                file.write(response.content)
                img_path = f"static/{client_id}-{cam_id}-{date_stamp}.jpg"
        else:
            print(f"Error downloading file: {response.status_code}")

        master_boxes = json.loads(master_boxes_json)

        response_data = {
            "datetime": formatted_dt,
            "imgurl": f"{request.url_root}{img_path}",
            "master_boxes": master_boxes
        }

        response_text = f"datetime: {formatted_dt}\n"
        response_text += f"imgurl: {request.url_root}{img_path}\n"

        for box in master_boxes:
            response_text += " ".join(str(x) for x in box) + "\n"

        response = make_response(response_text)
        response.headers.set('Content-Type', 'text/plain')
        return response

    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run()
