import numpy as np
import cv2
from yolo_segmentation import YOLOSegmentation
from shapely.geometry import Point, Polygon
import pymysql
import boto3
import json
import sys
import gzip
import os


class AgAIProcessor:
    def __init__(self, model_path, model, data_folder):
        self.model_path = model_path
        self.model = model
        self.data_folder = data_folder
        self.ys = YOLOSegmentation(model_path + model + ".pt")

    def get_values(self, frame_data):
        print("Processing Started!")

        global model_path
        global model
        self.ys = YOLOSegmentation(model_path + model + ".pt")

        image_count = 0
        total_cows = 0

        master_boxes = []

        coords_list = []

        normalized_data = cv2.normalize(frame_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        colored_data = cv2.applyColorMap(normalized_data, cv2.COLORMAP_BONE)

        img = colored_data
        cow_count = 0
        total_calves = 0
        calf_count = 0
        person_count = 0

        cow_number = 0

        bboxes, classes, segmentations, scores = self.ys.detect(img)
        for bbox, class_id, seg, score in zip(bboxes, classes, segmentations, scores):
            cow_number += 1

            (x, y, x2, y2) = bbox
            
            if class_id == 0:
                # label = "cow"
                cow_count += 1
            elif class_id == 1:
                # label = "cow"
                calf_count += 1
                cow_count += 1
            elif class_id == 2:
                # label = "person"
                person_count += 1

            # Get the center of the bounding box
            try:
                min_x = np.min(seg, axis=0)[0]
                max_x = np.max(seg, axis=0)[0]
                min_y = np.min(seg, axis=0)[1]
                max_y = np.max(seg, axis=0)[1]
                center_x = int((min_x + max_x) / 2)
                center_y = int((min_y + max_y) / 2)
            except ValueError:
                # Handle the case where the array is empty
                min_x = 0
                max_x = 0
                min_y = 0
                max_y = 0
                center_x = 0
                center_y = 0

            # Get the value at the center coordinates
            value = frame_data[center_y, center_x]

            # Define the polygon
            try:
                polygon = Polygon(seg)
            except ValueError:
                polygon = None

            # Define the list of values inside the polygon
            if polygon is not None:
                values_inside_polygon = []
                for i in range(240):
                    for j in range(320):
                        point = [j, i]
                        if polygon.contains(Point(point)):
                            # value = single_array[i, j]
                            value = frame_data[i, j]
                            values_inside_polygon.append(value)
            else:
                values_inside_polygon = None
            
            cv2.polylines(img, [seg], True, (0, 0, 255), 4)


            if values_inside_polygon is not None:
                mean_value = np.nanmean(values_inside_polygon)
                if np.isnan(mean_value):
                    # Handle the case when the mean value is NaN (e.g., set a default value)
                    mean_value = 0
            else:
                mean_value = None

            # Temperatures inside polygon
            if values_inside_polygon is not None:
                if len(values_inside_polygon) == 0:
                    temp_mean = 200
                else:
                    temp_mean = round(np.mean(values_inside_polygon), 1)
            else:
                temp_mean = None

            # Get all the temps inside polygon
            temp_all = []
            if values_inside_polygon is not None:
                for temp in values_inside_polygon:
                    temp_all.append(round(temp, 1))

            coords = [class_id, score, temp_mean]
            # print(coords)

            coords_list.append(coords)

            single_detected = []

            single_detected = [cow_number, score, temp_mean]
            # print(single_detected)
            master_boxes.append(single_detected)
        
        message = f"Processed image: {image_count + 1} with {cow_count} cows"

        print(message)


        image_count += 1

        total_cows = total_cows + (cow_count)
        total_calves = total_calves + calf_count
        
        return img, master_boxes

    def save_to_db(self, date_stamp, client_ID, cam_ID, comment, latitude, longitude, elevation, temperature, pressure, humidity, dew_point, relative_humidity, wetbulb_temp, heat_index, wind_speed, wind_deg, wind_chill, weather_type, weather_desc, cloud_coverage, model, master_boxes, img, array_data):
        print("saving to DB")

        image_path = data_folder + "/images/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".jpg"
        
        cv2.imwrite(image_path, img, [cv2.IMWRITE_JPEG_QUALITY, 65])

        # bucket_name = "agaicamstorage"

        # # Upload the compressed file to S3
        # obj = boto3.client('s3')
        # obj.upload_file(image_path, bucket_name, "images/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".jpg")

        # config = {
        #     'host': 'agaidatabase.cog2fppyk9lm.us-east-2.rds.amazonaws.com',
        #     'user': 'admin',
        #     'password': 'password',
        #     'database': 'agaidatabase'
        # }

        # # Connect to the MySQL server
        # print("Connecting to database...")
        # try:
        #     conn = pymysql.connect(
        #         host=config['host'],
        #         user=config['user'],
        #         password=config['password'],
        #         database=config['database']
        #     )
        #     print("Connection established")
        # except pymysql.err.OperationalError as err:
        #     if err.args[0] == 1045:  # Access denied error
        #         print("Something is wrong with the user name or password")
        #     elif err.args[0] == 1049:  # Unknown database error
        #         # Create the database if it does not exist
        #         conn = pymysql.connect(
        #             host=config['host'],
        #             user=config['user'],
        #             password=config['password']
        #         )
        #         cursor = conn.cursor()
        #         cursor.execute("CREATE DATABASE {}".format(config['database']))
        #         print("Database created")
        #         conn.close()
        #         # Reconnect to the newly created database
        #         conn = pymysql.connect(
        #             host=config['host'],
        #             user=config['user'],
        #             password=config['password'],
        #             database=config['database']
        #         )
        #     else:
        #         print(err)

        # cursor = conn.cursor()

        # cursor.execute(f"USE {config['database']}")

        # # Create the table if it doesn't already exist
        # table_name = f"client_{client_ID}"

        # cursor.execute(
        #     f"CREATE TABLE IF NOT EXISTS {table_name} "
        #     "(id INT AUTO_INCREMENT PRIMARY KEY, "
        #     "date_stamp VARCHAR(255) NOT NULL, "
        #     "client_id VARCHAR(255) NOT NULL, "
        #     "camera VARCHAR(255) NOT NULL, "
        #     "comment TEXT NOT NULL, "
        #     "lat FLOAT(10,6) NOT NULL, "
        #     "lon FLOAT(10,6) NOT NULL, "
        #     "elevation FLOAT(10,6) NOT NULL, "
        #     "temp FLOAT(10,6) NOT NULL, "
        #     "pressure FLOAT(10,6) NOT NULL, "
        #     "humidity FLOAT(10,6) NOT NULL, "
        #     "dew_point FLOAT(10,6) NOT NULL, "
        #     "relative_humidity FLOAT(10,6) NOT NULL, "
        #     "wetbulb_temp FLOAT(10,6) NOT NULL, "
        #     "heat_index FLOAT(10,6) NOT NULL, "
        #     "wind_speed FLOAT(10,6) NOT NULL, "
        #     "wind_deg INT NOT NULL, "
        #     "wind_chill FLOAT(10,6) NOT NULL, "
        #     "weather_type VARCHAR(255) NOT NULL, "
        #     "weather_desc VARCHAR(255) NOT NULL, "
        #     "cloud_coverage INT NOT NULL, "
        #     "model VARCHAR(255) NOT NULL, "
        #     "number_detected INT NOT NULL, "
        #     "list_of_detected_objects TEXT NOT NULL, "
        #     "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        # )

        # insert_query = (f"INSERT INTO {table_name} "
        #                 f"(date_stamp, client_id, camera, comment, lat, lon, elevation, temp, pressure, humidity, dew_point, relative_humidity, wetbulb_temp, heat_index, wind_speed, wind_deg, wind_chill, weather_type, weather_desc, cloud_coverage, model, number_detected, list_of_detected_objects)"
        #                 f"VALUES ('{date_stamp}', '{client_ID}', '{cam_ID}', '{comment}', {latitude}, {longitude}, {elevation}, {temperature}, {pressure}, {humidity}, {dew_point}, {relative_humidity}, {wetbulb_temp}, {heat_index}, {wind_speed}, {wind_deg}, {wind_chill}, '{weather_type}', '{weather_desc}', {cloud_coverage}, '{model}', {len(master_boxes)}, '{json.dumps(master_boxes)}')")

        # cursor.execute(insert_query)
        # conn.commit()
        # print("Inserted data")

        # # Clean up
        # cursor.close()
        # conn.close()


    def process_file(self, file_path):

        # Unzip the file
        # unzipped_file_path = file_path[:-3]  # Remove the '.gz' extension
        # with gzip.open(file_path, 'rb') as gzipped_file:
        #     with open(unzipped_file_path, 'wb') as unzipped_file:
        #         unzipped_file.write(gzipped_file.read())

        # with open(unzipped_file_path, 'r') as f:
        # # with open(file_path, 'r') as f:
        #     lines = f.readlines()
        #     if len(lines) < 2:
        #         print('Error: file does not contain metadata and data')

        with open(file_path, 'r') as f:
        # with open(file_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                print('Error: file does not contain metadata and data')
        
        
            
            info_line = lines[0]

            data = {key_value.split(':')[0]: key_value.split(':')[1] for key_value in info_line.split(',')}

            date_stamp = data['date_stamp']
            client_ID = data['client_ID']
            cam_ID = data['cam_ID']
            comment = data['comment']
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            elevation = int(data['elevation'])
            temperature = float(data['temperature'])
            pressure = int(data['pressure'])
            humidity = int(data['humidity'])
            dew_point = float(data['dew_point'])
            relative_humidity = float(data['relative_humidity'])
            wetbulb_temp = float(data['wetbulb_temp'])
            heat_index = float(data['heat_index'])
            wind_speed = float(data['wind_speed'])
            wind_deg = int(data['wind_deg'])
            wind_chill = float(data['wind_chill'])
            weather_type = data['weather_type']
            weather_desc = data['weather_desc']
            cloud_coverage = int(data['cloud_coverage'])

            array_data = np.loadtxt(lines[1:], delimiter=' ')
            # print('Loaded data from file:', unzipped_file_path)

            img, master_boxes = self.get_values(array_data)
            self.save_to_db(date_stamp, client_ID, cam_ID, comment, latitude, longitude, elevation, temperature, pressure, humidity, dew_point, relative_humidity, wetbulb_temp, heat_index, wind_speed, wind_deg, wind_chill, weather_type, weather_desc, cloud_coverage, model, master_boxes, img, array_data)

        # Delete the unzipped file after processing
        # os.remove(unzipped_file_path)

if __name__ == "__main__":
    data_folder = "/home/agai/Documents/awstest"
    model_path = '/home/agai/code/AgAI_CS/models/'
    model = 'v8sSeg3_6_23'
    file_path = sys.argv[1]

    processor = AgAIProcessor(model_path, model, data_folder)
    processor.process_file(file_path)

