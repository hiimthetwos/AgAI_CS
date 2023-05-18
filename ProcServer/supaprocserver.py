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
import shutil
from sqlalchemy import create_engine, text
import json
from supabase import create_client, Client


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
            
            # Draw the polygon
            cv2.polylines(img, [seg], True, (0, 0, 255), 4)

            # Draw the bounding box
            # cv2.rectangle(img, (x, y), (x2, y2), (255, 0, 0), 2)

            # Write the Temperature on the image
            # cv2.putText(img, (str(label) + " " + str(int(np.mean(values_inside_polygon))) + "C"), (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

            cv2.putText(img, ("# "  + str(cow_number)), (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)



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

        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        if not os.path.exists(data_folder + "/images"):
            os.makedirs(data_folder + "/images")
        
        cv2.imwrite(image_path, img, [cv2.IMWRITE_JPEG_QUALITY, 65])

        # bucket_name = "agaicamstorage"

        # # Upload the compressed file to S3
        # obj = boto3.client('s3')
        # obj.upload_file(image_path, bucket_name, "images/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".jpg")

        # config = {
        #     'url': 'julpecwjphvofyljbfnf.supabase.co',
        #     'anon_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHBlY3dqcGh2b2Z5bGpiZm5mIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODM1OTg2ODAsImV4cCI6MTk5OTE3NDY4MH0.vZLpRNSqRKlIT5W0Saqg3_xL8xZFb5Ic2jALHFBr3WQ'
        # }

        # DATABASE_URL = f"postgresql://{config['anon_key']}@{config['url']}/postgres"

        # engine = create_engine(DATABASE_URL)

        # with engine.connect() as connection:
        #     insert_query = text(f"""
        #     INSERT INTO cameradata
        #     (date_stamp, client_id, camera, comment, lat, lon, elevation, temp, pressure, humidity, dew_point, relative_humidity, wetbulb_temp, heat_index, wind_speed, wind_deg, wind_chill, weather_type, weather_desc, cloud_coverage, model, number_detected, list_of_detected_objects)
        #     VALUES (:date_stamp, :client_id, :camera, :comment, :lat, :lon, :elevation, :temp, :pressure, :humidity, :dew_point, :relative_humidity, :wetbulb_temp, :heat_index, :wind_speed, :wind_deg, :wind_chill, :weather_type, :weather_desc, :cloud_coverage, :model, :number_detected, :list_of_detected_objects)
        #     """)

        #     connection.execute(insert_query, date_stamp=date_stamp, client_id=client_ID, camera=cam_ID, comment=comment, lat=latitude, lon=longitude, elevation=elevation, temp=temperature, pressure=pressure, humidity=humidity, dew_point=dew_point, relative_humidity=relative_humidity, wetbulb_temp=wetbulb_temp, heat_index=heat_index, wind_speed=wind_speed, wind_deg=wind_deg, wind_chill=wind_chill, weather_type=weather_type, weather_desc=weather_desc, cloud_coverage=cloud_coverage, model=model, number_detected=len(master_boxes), list_of_detected_objects=json.dumps(master_boxes))

        #     print("Inserted data")

        # SUPABASE_URL = os.environ.get("SUPABASE_URL")
        # SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

        SUPABASE_URL = "https://julpecwjphvofyljbfnf.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1bHBlY3dqcGh2b2Z5bGpiZm5mIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODM1OTg2ODAsImV4cCI6MTk5OTE3NDY4MH0.vZLpRNSqRKlIT5W0Saqg3_xL8xZFb5Ic2jALHFBr3WQ"

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        data, error = supabase.table('cameradata').insert([
            {
                "date_stamp": date_stamp,
                "client_id": client_ID,
                "camera": cam_ID,
                "comment": comment,
                "lat": latitude,
                "lon": longitude,
                "elevation": elevation,
                "temp": temperature,
                "pressure": pressure,
                "humidity": humidity,
                "dew_point": dew_point,
                "relative_humidity": relative_humidity,
                "wetbulb_temp": wetbulb_temp,
                "heat_index": heat_index,
                "wind_speed": wind_speed,
                "wind_deg": wind_deg,
                "wind_chill": wind_chill,
                "weather_type": weather_type,
                "weather_desc": weather_desc,
                "cloud_coverage": cloud_coverage,
                "model": model,
                "number_detected": len(master_boxes),
                "list_of_detected_objects": json.dumps(master_boxes)
            }
        ]).execute()

        print("Inserted data")



    def process_file(self, file_path):
            
        # Unzip the file
        file_name = os.path.basename(file_path)
        unzipped_file_name = file_name[:-3]  # Remove the '.gz' extension
        destination_folder = '/mnt/data/tmp'
        os.makedirs(destination_folder, exist_ok=True)
        unzipped_file_path = os.path.join(destination_folder, unzipped_file_name)

        with gzip.open(file_path, 'rb') as gzipped_file:
            with open(unzipped_file_path, 'wb') as unzipped_file:
                unzipped_file.write(gzipped_file.read())

        with open(unzipped_file_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                print('Error: file does not contain metadata and data')


        # # Unzip the file
        # unzipped_file_path = file_path[:-3]  # Remove the '.gz' extension
        # with gzip.open(file_path, 'rb') as gzipped_file:
        #     with open(unzipped_file_path, 'wb') as unzipped_file:
        #         unzipped_file.write(gzipped_file.read())

        # with open(unzipped_file_path, 'r') as f:
        # # with open(file_path, 'r') as f:
        #     lines = f.readlines()
        #     if len(lines) < 2:
        #         print('Error: file does not contain metadata and data')


        # # Process a csv
        # with open(file_path, 'r') as f:
        # # with open(file_path, 'r') as f:
        #     lines = f.readlines()
        #     if len(lines) < 2:
        #         print('Error: file does not contain metadata and data')
        
        
            
            info_line = lines[0]

            data = {key_value.split(':')[0]: key_value.split(':')[1] for key_value in info_line.split(',')}

            date_stamp = data['date_stamp']
            # client_ID = data['client_ID']
            client_ID= "a1"
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

        # Delete the unzipped file from the temp folder
        os.remove(unzipped_file_path)

        # Move the zipped file to /mnt/data/stored and delete it from its current location
        stored_folder = '/mnt/data/stored'
        os.makedirs(stored_folder, exist_ok=True)
        stored_file_path = os.path.join(stored_folder, file_name)
        shutil.move(file_path, stored_file_path)

if __name__ == "__main__":
    data_folder = "/mnt/data"
    model_path = '/home/agai/code/AgAI_CS/models/'
    model = 'v8sSeg3_6_23'
    file_path = sys.argv[1]

    processor = AgAIProcessor(model_path, model, data_folder)
    processor.process_file(file_path)
