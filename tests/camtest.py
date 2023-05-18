import numpy as np
import time
import os
import datetime
import requests
import gzip
import math
import boto3
import cv2

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
        # self.save_root = "/home/agai/test/test"
        self.save_root = "/mnt/data/test"

        self.save_folder= self.save_root + "/"
        self.next_call = time.time()
        self.camera_id = ""
        self.bucket_name = "agaicamstorage"
        self.cap_interval = 5 # in seconds

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

        # if not os.path.exists(self.save_root):
        #     os.makedirs(self.save_root)


    def calculate_relative_humidity(self, temperature, dew_point_temperature):
        # Calculate actual vapor pressure
        actual_vapor_pressure = 6.112 * math.exp((17.67 * dew_point_temperature) / (dew_point_temperature + 243.5))
        
        # Calculate saturation vapor pressure
        saturation_vapor_pressure = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
        
        # Calculate relative humidity
        relative_humidity = (actual_vapor_pressure / saturation_vapor_pressure) * 100.0
        
        return round(relative_humidity, 2)


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

        # image_path = "/home/agai/test/test/test.jpg"
        image_path = "/mnt/data/test/test.jpg"


        normalized_data = cv2.normalize(therm_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        colored_data = cv2.applyColorMap(normalized_data, cv2.COLORMAP_BONE)
        
        cv2.imwrite(image_path, colored_data, [cv2.IMWRITE_JPEG_QUALITY, 65])

    
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
            image_path = "/mnt/data/test/test.jpg"

            normalized_data = cv2.normalize(therm_frame.data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            colored_data = cv2.applyColorMap(normalized_data, cv2.COLORMAP_BONE)
        
            cv2.imwrite(image_path, colored_data, [cv2.IMWRITE_JPEG_QUALITY, 65])
            print("wrote image")

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
