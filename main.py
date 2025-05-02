# Import necessary libraries
import openmeteo_requests                # API client for Open-Meteo weather data
import requests_cache                    # Caching library to save API responses locally
import pandas as pd                      # Pandas for managing time series and tabular data
from retry_requests import retry         # Auto-retry failed HTTP requests
from geopy.geocoders import Nominatim    # Library to convert city names to latitude/longitude

# Function to get coordinates (latitude, longitude) and full location name from a city name
def get_coordinates_from_city(city):
    geolocator = Nominatim(user_agent="weather_app")         # Set up a geolocation service
    location = geolocator.geocode(city)                      # Look up the city
    if location:
        return location.latitude, location.longitude, location.address
    else:
        raise ValueError("City not found")                   # Raise an error if city not found

# Function to fetch and display the weather forecast for a given city
def get_weather(city_name):
    # ✅ FIXED: Unpack all three values returned by get_coordinates_from_city
    latitude, longitude, full_location = get_coordinates_from_city(city_name)

    # Set up cached and retryable session for the API
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=10, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Define Open-Meteo API request
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m",
        "timezone": "auto"  # Automatically match local time
    }

    # Call the weather API
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]  # Get the first response (only one location expected)

    # Display location information
    print(f"\n📍 Weather Forecast for {full_location}:")
    print(f"  Coordinates: {response.Latitude()}°N, {response.Longitude()}°E")
    print(f"  Elevation: {response.Elevation()} m")
    print(f"  Timezone: {response.Timezone().decode()} ({response.TimezoneAbbreviation().decode().replace('GMT', 'UTC')})")

    # Process hourly temperature data
    hourly = response.Hourly()
    hourly_temperature = hourly.Variables(0).ValuesAsNumpy()

    # Generate timestamps for hourly data
    hourly_times = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )

    # Display hourly temperature forecast
    print("\n🌡 Hourly Temperature Forecast (°C):")
    for i in range(24):  # First 24 hours only
        time_str = hourly_times[i].strftime("%H:%M")
        temp = hourly_temperature[i]
        print(f"  {time_str} — {temp:.1f}°C")

# App entry point
def main():
    print("=== Weather Forecast App ===")
    while True:
        # Ask for city input
        city = input("\nEnter city name (or type 'exit' to quit): ").strip()
        if city.lower() == 'exit':
            print("Goodbye!")
            break
        try:
            get_weather(city)
        except ValueError as ve:
            print(f"Error: {ve}")
        except Exception as e:
            print(f"Unexpected error: {e}")

# Run the app if the script is executed
if __name__ == "__main__":
    main()
