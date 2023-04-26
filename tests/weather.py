import requests
import math

# Enter your OpenWeatherMap API key
api_key = "f32b18bc1330c560ccd52deed8f94ded"

# Enter the latitude and longitude of the location you want to check the weather for
lat = "46.3346"
lon = "-113.3022"


def calculate_relative_humidity(temperature, dew_point_temperature):
    # Calculate actual vapor pressure
    actual_vapor_pressure = 6.112 * math.exp((17.67 * dew_point_temperature) / (dew_point_temperature + 243.5))
    
    # Calculate saturation vapor pressure
    saturation_vapor_pressure = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
    
    # Calculate relative humidity
    relative_humidity = (actual_vapor_pressure / saturation_vapor_pressure) * 100.0
    
    return round(relative_humidity, 2)


def calculate_wetbulb_temperature(temperature, relative_humidity, pressure):
    # Calculate saturation vapor pressure
    saturation_vapor_pressure = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
    
    # Calculate vapor pressure deficit
    vapor_pressure_deficit = saturation_vapor_pressure - (relative_humidity / 100.0) * saturation_vapor_pressure
    
    # Calculate wet-bulb depression
    wetbulb_depression = 234.5 * vapor_pressure_deficit / (1005 + 1.84 * temperature - vapor_pressure_deficit)
    
    # Calculate wet-bulb temperature
    wetbulb_temperature = temperature - wetbulb_depression
    
    return round(wetbulb_temperature, 2)


def calculate_heat_index(temperature, relative_humidity):
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


def calculate_wind_chill(temperature, windspeed):
    # Calculate wind chill
    wind_chill = 35.74 + 0.6215 * temperature - 35.75 * windspeed ** 0.16 + 0.4275 * temperature * windspeed ** 0.


# Make a request to the OpenWeatherMap API to get the weather data for the specified location
weather_url = f"http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,daily&units=imperial&appid={api_key}"
weather_response = requests.get(weather_url)
weather_data = weather_response.json()

# Get the current temperature, pressure, humidity, cloud coverage, and precipitation from the weather data
current_data = weather_data["current"]
temperature = current_data["temp"]
pressure = current_data["pressure"]
humidity = current_data["humidity"]
dew_point = current_data["dew_point"]
relative_humidity = calculate_relative_humidity(temperature, dew_point)
wetbulb_temp = calculate_wetbulb_temperature(temperature, relative_humidity, pressure)
heat_index = calculate_heat_index(temperature, relative_humidity)
wind_speed = current_data["wind_speed"]
wind_deg = current_data["wind_deg"]
wind_chill = calculate_wind_chill(temperature, wind_speed)
cloud_coverage = current_data["clouds"]
weather_type = current_data["weather"][0]["main"]
weather_desc = current_data["weather"][0]["description"]
# precipitation = current_data.get("rain", 0) + current_data.get("snow", 0)

print(f"Temperature: {temperature}")
print(f"Pressure: {pressure}")
print(f"Humidity: {humidity}")
print(f"Relative Humidity: {relative_humidity}")
print(f"Wetbulb Temperature: {wetbulb_temp}")
print(f"Wind Chill: {wind_chill}")
print(f"Heat Index: {heat_index}")
print(f"Cloud coverage: {cloud_coverage}")
print(f"Dew point: {dew_point}")
print(f"Wind speed: {wind_speed}")
print(f"Wind deg: {wind_deg}")
print(f"Weather Type: {weather_type}")
print(f"Weather Description: {weather_desc}")
# print(f"Precipitation: {precipitation}")

start = 1664528400
end = 1664553600
hist_data = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={api_key}"
hist_response = requests.get(weather_url)
hist_data = weather_response.json()
print(hist_data)