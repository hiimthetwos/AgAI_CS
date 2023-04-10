import numpy as np
import time
import os
import datetime
import requests
import gzip
import math
import boto3

from datetime import datetime
from time import sleep

from seekcamera import (
    SeekCameraIOType,
    SeekCameraManager,
    SeekCameraManagerEvent,
    SeekCameraFrameFormat,
)


class ThermalCamera:
    def __init__(self):
        self.saved_name = ""
        self.save_root = "/tmp/cameradata"
        self.save_folder= self.save_root + "/"
        self.next_call = time.time()
        self.camera_id = ""
        self.bucket_name = "agaicamstorage"
        self.cap_interval = 1 # in seconds

        # self.temp, self.humidity, self.pressure, self.altitude, self.dew_point, self.eq_sea_level_pressure, self.heat_index, self.abs_humidity = self.read_serial_data()

        self.client_id = "aa11"
        self.cam_id = self.camera_id
        self.comment = ""
        self.latitude = "46.2319"
        self.longitude = "-113.3781"
        self.altitude = "0"
        # self.elevation = str(int((self.altitude) * 3.28084))
        self.elevation = 5430
        self.api_key = "f32b18bc1330c560ccd52deed8f94ded"

        if not os.path.exists(self.save_root):
            os.makedirs(self.save_root)


    def calculate_relative_humidity(self, temperature, dew_point_temperature):
        # Calculate actual vapor pressure
        actual_vapor_pressure = 6.112 * math.exp((17.67 * dew_point_temperature) / (dew_point_temperature + 243.5))
        
        # Calculate saturation vapor pressure
        saturation_vapor_pressure = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
        
        # Calculate relative humidity
        relative_humidity = (actual_vapor_pressure / saturation_vapor_pressure) * 100.0
        
        return round(relative_humidity, 2)


    def calculate_wetbulb_temperature(self, temperature, relative_humidity, pressure):
        # Calculate saturation vapor pressure
        saturation_vapor_pressure = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
        
        # Calculate vapor pressure deficit
        vapor_pressure_deficit = saturation_vapor_pressure - (relative_humidity / 100.0) * saturation_vapor_pressure
        
        # Calculate wet-bulb depression
        wetbulb_depression = 234.5 * vapor_pressure_deficit / (1005 + 1.84 * temperature - vapor_pressure_deficit)
        
        # Calculate wet-bulb temperature
        wetbulb_temperature = temperature - wetbulb_depression
        
        return round(wetbulb_temperature, 2)


    def calculate_heat_index(self, temperature, relative_humidity):
        # Calculate heat index
        heat_index = -42.379 + (2.04901523 * temperature) + (10.14333127 * relative_humidity) - (0.22475541 * temperature * relative_humidity) - (6.83783 * 10 ** -3 * temperature ** 2) - (5.481717 * 10 ** -2 * relative_humidity ** 2) + (1.22874 * 10 ** -3 * temperature ** 2 * relative_humidity) + (8.5282 * 10 ** -4 * temperature * relative_humidity ** 2) - (1.99 * 10 ** -6 * temperature ** 2 * relative_humidity ** 2)
        
        # Adjust for low relative humidity
        if relative_humidity < 13 and temperature >= 80 and temperature <= 112:
            adjustment = ((13 - relative_humidity) / 4) * math.sqrt((17 - abs(temperature - 95)) / 17)
            heat_index += adjustment
        
        # Adjust for high relative humidity
        elif relative_humidity > 85 and temperature >= 80 and temperature <= 87:
            adjustment = ((relative_humidity - 85) / 10) * ((87 - temperature) / 5)
            heat_index -= adjustment
        
        return round(heat_index, 2)


    def calculate_wind_chill(self, temperature, windspeed):
        # Calculate wind chill
        wind_chill = 35.74 + 0.6215 * temperature - 35.75 * windspeed ** 0.16 + 0.4275 * temperature * windspeed ** 0.16
        
        return round(wind_chill, 2)


    def write_file(self, date, cam_ID, data):
        date_stamp = date
        client_ID = self.client_id
        comment = self.comment
        latitude = self.latitude
        longitude = self.longitude
        elevation = self.elevation

        # Get the current temperature, pressure, humidity, cloud coverage, and precipitation from the weather data
        temperature, pressure, humidity, dew_point, relative_humidity, wetbulb_temp, heat_index, wind_speed, wind_deg, wind_chill, weather_type, weather_desc, cloud_coverage = self.get_weather()

        # Convert numpy array to float16
        therm_data = data.astype(np.float16)

        # Create file name
        file_name = self.save_folder + client_ID + "-" + cam_ID + "-" + date_stamp + ".csv"

        # Write data to file
        with open(file_name, 'w') as f:
            # f.write(f"{date_stamp},{client_ID},{cam_ID},{comment},{latitude},{longitude},{elevation},{temperature},{pressure},{humidity},{dew_point},{relative_humidity},{wetbulb_temp},{heat_index},{wind_speed},{wind_deg},{wind_chill},{weather_type},{weather_desc},{cloud_coverage}\n")
            f.write(f"date_stamp:{date_stamp},client_ID:{client_ID},cam_ID:{cam_ID},comment:{comment},latitude:{latitude},longitude:{longitude},elevation:{elevation},temperature:{temperature},pressure:{pressure},humidity:{humidity},dew_point:{dew_point},relative_humidity:{relative_humidity},wetbulb_temp:{wetbulb_temp},heat_index:{heat_index},wind_speed:{wind_speed},wind_deg:{wind_deg},wind_chill:{wind_chill},weather_type:{weather_type},weather_desc:{weather_desc},cloud_coverage:{cloud_coverage}\n")

            # How to read that line.
            # data = {key_value.split(':')[0]: key_value.split(':')[1] for key_value in line.split(',')}
            # print(data["date_stamp"])  # Output: 20230408-191325
            # print(data["client_ID"])  # Output: 00001
            # ... and so on for other variables


            np.savetxt(f, therm_data, delimiter=' ', fmt="%.1f")

        comp_file_name = self.save_folder + client_ID + "-" + cam_ID + "-" + date_stamp + ".csv.gz"

        # Save the CSV file as a compressed file
        with gzip.open(comp_file_name, "wb") as compressed_file:
            # Read the contents of the CSV file
            with open(file_name, 'r') as original_file:
                content = original_file.read()

            # Write the content as bytes to the compressed file
            compressed_file.write(content.encode('utf-8'))

        obj = boto3.client('s3')

        # Upload the compressed file to S3
        obj.upload_file(comp_file_name, self.bucket_name, "uploaded/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".csv.gz")
        # obj.upload_file(file_name, self.bucket_name, "uploaded/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".csv")

        print("File uploaded to S3")
        
        # Remove the original CSV file
        os.remove(comp_file_name)


    
    def on_frame(self, camera, camera_frame, file):
        """Async callback fired whenever a new frame is available.

        Parameters
        ----------
        camera: SeekCamera
            Reference to the camera for which the new frame is available.
        camera_frame: SeekCameraFrame
            Reference to the class encapsulating the new frame (potentially
            in multiple formats).
        file: TextIOWrapper
            User defined data passed to the callback. This can be anything
            but in this case it is a reference to the open CSV file to which
            to log data.
        """

        # Get the thermography frame data
        therm_frame = camera_frame.thermography_float

        fahrenheit = np.zeros((therm_frame.height, therm_frame.width))
        fahrenheit[:] = therm_frame.data * 9/5 + 32

        fahr_data = fahrenheit.astype(np.float16)

        # get the camera id
        cam_ID = camera.chipid
        
        if time.time() >= self.next_call:
            now = datetime.now()
            date_stamp = now.strftime("%Y%m%d-%H%M%S")

            # self.write_file(date_stamp, cam_ID, therm_frame.data)
            self.write_file(date_stamp, cam_ID, fahr_data)

            # Set the next call time in seconds
            self.next_call = time.time() + self.cap_interval

    def on_event(self, camera, event_type, event_status, _user_data):
        """Async callback fired whenever a camera event occurs.

        Parameters
        ----------
        camera: SeekCamera
            Reference to the camera on which an event occurred.
        event_type: SeekCameraManagerEvent
            Enumerated type indicating the type of event that occurred.
        event_status: Optional[SeekCameraError]
            Optional exception type. It will be a non-None derived instance of
            SeekCameraError if the event_type is SeekCameraManagerEvent.ERROR.
        _user_data: None
            User defined data passed to the callback. This can be anything
            but in this case it is None.
        """
        print("{}: {}".format(str(event_type), camera.chipid))

        if event_type == SeekCameraManagerEvent.CONNECT:
            # Open a new CSV file
            try:
                # file = open(self.save_folder + "thermography-" + camera.chipid + ".csv", "a")
                file = open(self.save_folder + "thermography" + ".csv", "a")
            except OSError as e:
                print("Failed to open file: %s" % str(e))
                return

            # Start streaming data and provide a custom callback to be called
            # every time a new frame is received.
            camera.register_frame_available_callback(self.on_frame, file)
            camera.capture_session_start(SeekCameraFrameFormat.THERMOGRAPHY_FLOAT)

        elif event_type == SeekCameraManagerEvent.DISCONNECT:
            camera.capture_session_stop()

        elif event_type == SeekCameraManagerEvent.ERROR:
            print("{}: {}".format(str(event_status), camera.chipid))

        elif event_type == SeekCameraManagerEvent.READY_TO_PAIR:
            return


    def get_weather(self):
        # Make a request to the OpenWeatherMap API to get the weather data for the specified location
        weather_url = f"http://api.openweathermap.org/data/2.5/onecall?lat={self.latitude}&lon={self.longitude}&exclude=minutely,daily&units=imperial&appid={self.api_key}"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        current_data = weather_data["current"]
        temperature = current_data["temp"]
        pressure = current_data["pressure"]
        humidity = current_data["humidity"]
        dew_point = current_data["dew_point"]
        relative_humidity = self.calculate_relative_humidity(temperature, dew_point)
        wetbulb_temp = self.calculate_wetbulb_temperature(temperature, relative_humidity, pressure)
        heat_index = self.calculate_heat_index(temperature, relative_humidity)
        wind_speed = current_data["wind_speed"]
        wind_deg = current_data["wind_deg"]
        wind_chill = self.calculate_wind_chill(temperature, wind_speed)
        cloud_coverage = current_data["clouds"]
        weather_type = current_data["weather"][0]["main"]
        weather_desc = current_data["weather"][0]["description"]

        return temperature, pressure, humidity, dew_point, relative_humidity, wetbulb_temp, heat_index, wind_speed, wind_deg, wind_chill, weather_type, weather_desc, cloud_coverage

    def main(self):
        """Create a context structure responsible for managing all connected USB cameras.
            Cameras with other IO types can be managed by using a bitwise or of the
            SeekCameraIOType enum cases.
        """

        with SeekCameraManager(SeekCameraIOType.USB) as manager:
            # Start listening for events.
            manager.register_event_callback(self.on_event)

            while True:
                sleep(0)

# Run the Class
if __name__ == '__main__':
    thermal_camera = ThermalCamera()
    thermal_camera.main()
