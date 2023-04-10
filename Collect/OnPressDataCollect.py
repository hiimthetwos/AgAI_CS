import numpy as np
import time
import cv2
import os
import json
import gzip
import boto3
import requests
import json
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
        self.folder_date = datetime.now()
        self.folder_date = self.folder_date.strftime("%m_%d_%Y")
        self.saved_name = ""
        # self.save_root = "/home/ryanbert/Documents/data/" + self.folder_date + "/datacapture"
        self.save_root = "/home/ryanbert/Documents/data/" + self.folder_date
        self.save_folder= self.save_root + "/"
        self.next_call = time.time()
        self.camera_id = ""
        self.isPressed = False
        self.camera_id = ""
        self.bucket_name = "agaicamstorage"

        # self.client_id = "aa11"
        # self.comment = ""
        # self.latitude = 46.2083
        # self.longitude = -113.3934
        # self.elevation = 5611
        # self.altitude = 5611
        
        self.client_id = "aa11"
        self.cam_id = self.camera_id
        self.comment = ""
        self.latitude = "46.2083"
        self.longitude = "-113.3934"
        self.altitude = "0"
        # self.elevation = str(int((self.altitude) * 3.28084))
        self.elevation = 5430
        self.api_key = "f32b18bc1330c560ccd52deed8f94ded"

        
        
        # self.temp, self.humidity, self.pressure, self.altitude, self.dew_point, self.eq_sea_level_pressure, self.heat_index, self.abs_humidity = self.read_serial_data()
        # self.temp = 22.7
        # self.humidity = 74.57
        # self.pressure = 1001
        # self.altitude = 4665
        # self.temp = input("Enter Temperature in fahrenheit: ")

        # self.temp = 0
        # self.humidity = 0
        # self.pressure = 0
        # self.altitude = 0

        # self.input_weather_data()

        if not os.path.exists(self.save_root):
            os.makedirs(self.save_root)
        if not os.path.exists(self.save_root + "/images"):
            os.makedirs(self.save_root + "/images")

    
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

        # Save the thermal image
        self.saved_name = self.save_folder + "images/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".jpg"
        normalized_data = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        colored_data = cv2.applyColorMap(normalized_data, cv2.COLORMAP_BONE)
        # cv2.imshow("Thermal Image", colored_data)
        cv2.imwrite(self.saved_name, colored_data)

        obj = boto3.client('s3')

        # Upload the compressed file to S3
        obj.upload_file(self.saved_name, self.bucket_name, "collected/" + "images/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".jpg")
        # obj.upload_file(file_name, self.bucket_name, "uploaded/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".csv")

        print("Image uploaded to S3")

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
        obj.upload_file(comp_file_name, self.bucket_name, "collected/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".csv.gz")
        # obj.upload_file(file_name, self.bucket_name, "uploaded/" + client_ID + "-" + cam_ID + "-" + date_stamp + ".csv")

        print("File uploaded to S3")
        
        # Remove the original CSV file
        # os.remove(comp_file_name)

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


    def input_weather_data(self):
        while True:
            self.temp = input("Enter Temperature in fahrenheit with one decimal place: ")
            if self.temp.isdecimal() or self.temp.count('.') != 1 or len(self.temp.split('.')[1]) != 1:
                # If the input string is not a decimal number with one decimal place, ask again
                print("Invalid input, please try again.")
            else:
                # If the input string is valid, convert it to a float and break out of the loop
                self.temp = float(self.temp)
                break
        # self.humidity = input("Enter Humidity in %: ")
        while True:
            self.humidity = input("Enter humidity with one decimal place: ")
            if self.humidity.isdecimal() or self.humidity.count('.') != 1 or len(self.humidity.split('.')[1]) != 1:
                # If the input string is not a decimal number with one decimal place, ask again
                print("Invalid input, please try again.")
            else:
                # If the input string is valid, convert it to a float and break out of the loop
                self.humidity = float(self.humidity)
                break
        while True:
            self.pressure = input("Enter pressure in hPa with one decimal place: ")
            if self.pressure.isdecimal() or self.pressure.count('.') != 1 or len(self.pressure.split('.')[1]) != 1:
                # If the input string is not a decimal number with one decimal place, ask again
                print("Invalid input, please try again.")
            else:
                # If the input string is valid, convert it to a float and break out of the loop
                self.pressure = float(self.pressure)
                break
        # self.altitude = input("Enter Altitude in ft: ")
        # while True:
        #     self.pressure = input("Enter Pressure in hPa (four digits): ")
        #     if not self.pressure.isdigit() or len(self.pressure) != 4:
        #         # If the input string is not a four-digit number, ask again
        #         print("Invalid input, please enter a four-digit number.")
        #     else:
        #         # If the input string is valid, break out of the loop
        #         break        
        self.altitude = input("Enter Altitude in ft: ")


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
        
        # get the camera id
        self.camera_id = camera.chipid

        therm_frame = camera_frame.thermography_float

        fahrenheit = np.zeros((therm_frame.height, therm_frame.width))
        fahrenheit[:] = therm_frame.data * 9/5 + 32

        fahr_data = fahrenheit.astype(np.float16)

        # get the camera id
        cam_ID = camera.chipid

        # Create Image for Video
        normalized_data = cv2.normalize(therm_frame.data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        colored_data = cv2.applyColorMap(normalized_data, cv2.COLORMAP_BONE)
        frame200 = self.rescale_frame(colored_data, percent=200)
        cv2.imshow("Thermal Image", frame200) # Show the thermal image using OpenCV
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            os._exit(0)
        elif cv2.waitKey(32) & 0xFF == ord(' '):
            # now = datetime.now()
            # date_stamp = now.strftime("%Y%m%d-%H%M%S")
            # # Write the datestamp to the file
            # file.write(date_stamp + "\n")
            # # Write the thermal data to the file
            # fahrenheit = np.zeros((therm_frame.height, therm_frame.width))
            # fahrenheit[:] = therm_frame.data * 9/5 + 32
            # # np.savetxt(file, therm_frame.data, fmt="%.1f")
            # np.savetxt(file, fahrenheit, fmt="%.1f")

            # # Save the thermal image
            # self.saved_name = self.save_folder + "images/" + str(date_stamp) + ".jpg"
            # normalized_data = cv2.normalize(therm_frame.data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            # colored_data = cv2.applyColorMap(normalized_data, cv2.COLORMAP_BONE)
            # # cv2.imshow("Thermal Image", colored_data)
            # cv2.imwrite(self.saved_name, colored_data)

            # # Write the weather and client data to the file
            # self.write_weather_values(date_stamp)
            # self.client_details(date_stamp)
            
            now = datetime.now()
            date_stamp = now.strftime("%Y%m%d-%H%M%S")

            # self.write_file(date_stamp, cam_ID, therm_frame.data)
            self.write_file(date_stamp, cam_ID, fahr_data)
     
            print("Data Saved!")

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
                file = open(self.save_folder + "thermography-" + self.folder_date + ".csv", "a")
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

    def client_details(self, dateandtime):
        """Set the client details

        Parameters
        ----------
        dateandtime: string
            The date and time of the capture
        """

        client_id = "00001"
        cam_id = self.camera_id
        comment = ""
        latitude = "46.2319"
        longitude = "-113.3781"
        # elevation = str(int((self.altitude) * 3.28084))
        elevation = self.altitude
        
        # Create the filename
        filename = self.save_folder + 'clientdetails.json'

        # Check if the file exists, create it if not
        if not os.path.isfile(filename):
            with open(filename, 'w') as f:
                json.dump([], f)

        # Read the existing data from the file
        with open(filename, 'r') as f:
            data = json.load(f)

        client_values = [dateandtime, client_id, cam_id, comment, latitude, longitude, elevation]

        # Append the new weather values to the existing data
        data.append(client_values)

        # Write the updated data back to the file
        with open(filename, 'w') as f:
            json.dump(data, f)

    def rescale_frame(self, frame, percent=75):
        """Rescale the frame
        
        Parameters
        ----------
        frame: numpy.ndarray
            The frame to be rescaled
        percent: int
            The percentage to rescale the frame by
        """

        width = int(frame.shape[1] * percent/ 100)
        height = int(frame.shape[0] * percent/ 100)
        dim = (width, height)
        return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    def read_serial_data(self, port='/dev/ttyACM0', baudrate=9600):
        """Read the serial data from the Arduino
        
        Parameters
        ----------
        port: string
            The port to read the data from
            baudrate: int
            The baudrate to read the data at
                
        Returns
        -------
        temp: float
            The temperature in degrees C
        humidity: float
            The humidity in %
        pressure: float
            The pressure in hPa
        altitude: float
            The altitude in m
        dew_point: float
            The dew point in degrees C
        eq_sea_level_pressure: float
            The equivalent sea level pressure in hPa
        heat_index: float
            The heat index in degrees C
        abs_humidity: float
            The absolute humidity in g/m^3
        """

        ser = serial.Serial(port, baudrate)
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').rstrip()
                values = line.split('\t')
                if len(values) == 8:
                    try:
                        temp = float(values[0].split(':')[1])
                        humidity = float(values[1].split(':')[1])
                        pressure = float(values[2].split(':')[1])
                        altitude = float(values[3].split(':')[1])
                        dew_point = values[4].split(':')[1]
                        eq_sea_level_pressure = float(values[5].split(':')[1])
                        heat_index = float(values[6].split(':')[1])
                        abs_humidity = float(values[7].split(':')[1])
                        return temp, humidity, pressure, altitude, dew_point, eq_sea_level_pressure, heat_index, abs_humidity
                    except (ValueError, IndexError):
                        pass
                break

    def write_weather_values(self, dateandtime):
        """Write the weather values to a JSON file
        
        Parameters
        ----------
        dateandtime: string
            The date and time of the capture
        """

        filename = self.save_folder + 'weathervalues.json'

        # Check if the file exists, create it if not
        if not os.path.isfile(filename):
            with open(filename, 'w') as f:
                json.dump([], f)

        # Read the existing data from the file
        with open(filename, 'r') as f:
            datajs = json.load(f)

        # temp, humidity, pressure, altitude, dew_point, eq_sea_level_pressure, heat_index, abs_humidity = self.read_serial_data()

        # temp = 7.2222222222222
        print("Temperature: %0.1f C" % self.temp)
        # pressure = 1007.7892672000099
        print("Pressure: %0.1f hPa" % self.pressure)
        # humidity =  48.200000000000000
        print("Humidity: %0.1f %%" % self.humidity)

        # Create a new dictionary for the weather values
        weather_values = [dateandtime, self.temp, self.pressure, self.humidity]

        # Append the new weather values to the existing data
        datajs.append(weather_values)

        # Write the updated data back to the file
        with open(filename, 'w') as f:
            json.dump(datajs, f)

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