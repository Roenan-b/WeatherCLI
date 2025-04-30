# Import necessary libraries
import openmeteo_requests                # API client for Open-Meteo weather data
import requests_cache                    # Caching library to save API responses locally
import pandas as pd                      # Pandas for managing time series and tabular data
from retry_requests import retry          # Auto-retry failed HTTP requests
from geopy.geocoders import Nominatim     # Library to convert city names to latitude/longitude

# Function to get coordinates (latitude, longitude) and full location name from a city name
def get_coordinates_from_city(city):
    geolocator = Nominatim(user_agent="weather_app")  # Set up a geolocation service with a custom user agent
    location = geolocator.geocode(city)               # Query the location based on the input city name
    if location:
        return location.latitude, location.longitude, location.address  # Return coordinates and full address
    else:
        raise ValueError("City not found")            # Raise an error if no location is found

# Function to fetch and display the weather forecast for a given city
def get_weather(city_name):
    # Get latitude, longitude, and address for the city
    latitude, longitude= get_coordinates_from_city(city_name)

    # Set up a cached session to reduce API calls (caches for 1 hour)
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    # Add retry logic to automatically retry failed requests
    retry_session = retry(cache_session, retries=10, backoff_factor=0.2)
    # Initialize Open-Meteo client with retry-capable session
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # URL for the Open-Meteo weather API
    url = "https://api.open-meteo.com/v1/forecast"
    # Parameters for the weather API call
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m",  # Request hourly temperature
        "timezone": "auto"           # Automatically adjust to local timezone
    }

    # Make the API call and get a list of responses (one per location)
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]  # Get the first (and only) location's response

    # Print location info
    print(f"\n📍 Weather Forecast for {city_name}:")
    print(f"  Coordinates: {response.Latitude()}°N, {response.Longitude()}°E")
    print(f"  Elevation: {response.Elevation()} m")
    print(f"  Timezone: {response.Timezone().decode()} ({response.TimezoneAbbreviation().decode()})")  # Decode byte strings

    # Process hourly temperature data
    hourly = response.Hourly()  # Get hourly weather data container
    hourly_temperature = hourly.Variables(0).ValuesAsNumpy()  # Get temperatures as a NumPy array

    # Create a Pandas date range for each hourly forecasted temperature
    hourly_times = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),  # Start time
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),  # End time
        freq=pd.Timedelta(seconds=hourly.Interval()),             # Frequency (usually 1 hour)
        inclusive="left"                                          # Include the start time
    )

    # Print the hourly temperatures
    print("\n🌡 Hourly Temperature Forecast (°C):")
    for i in range(24):  # Only show the next 24 hours
        time_str = hourly_times[i].strftime("%H:%M")  # Format the time as HH:MM
        temp = hourly_temperature[i]                 # Get the corresponding temperature
        print(f"  {time_str} — {temp:.1f}°C")          # Print nicely formatted

# Main function that runs the app
def main():
    print("=== Weather Forecast App ===")
    while True:
        # Prompt user to enter a city name (or exit)
        city = input("\nEnter city name (or type 'exit' to quit): ").strip()
        if city.lower() == 'exit':  # If the user types 'exit', end the loop
            print("Goodbye!")
            break
        try:
            get_weather(city)  # Try fetching weather for the entered city
        except ValueError as ve:
            print(f"Error: {ve}")  # Handle case when city is not found
        except Exception as e:
            print(f"Unexpected error: {e}")  # Handle any other unexpected errors

# Entry point of the script
if __name__ == "__main__":
    main()
