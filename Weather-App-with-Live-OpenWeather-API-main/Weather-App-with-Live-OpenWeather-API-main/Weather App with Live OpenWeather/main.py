
import os
import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5"

CACHE_FILE = Path(__file__).parent / "weather_cache.json"

CACHE_SECONDS = 600  # Cache for 10 minutes


# Load cached weather data
def load_cache():

    if not CACHE_FILE.exists():
        return {}

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


# Save cached weather data
def save_cache(cache):

    with CACHE_FILE.open("w", encoding="utf-8") as file:
        json.dump(cache, file, indent=4)


# Fetch weather data from API
def get_weather_data(city):

    if not API_KEY:
        print("API key missing. Check your .env file.")
        return None

    cache = load_cache()

    cache_key = city.strip().lower()

    current_time = time.time()

    # Check cached data
    cached = cache.get(cache_key)

    if cached and current_time - cached.get("timestamp", 0) < CACHE_SECONDS:

        print("\nUsing cached weather data...")
        return cached.get("data")

    parameters = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        # Current weather request
        current_response = requests.get(
            f"{BASE_URL}/weather",
            params=parameters,
            timeout=15
        )

        if current_response.status_code == 404:
            print("City not found. Please check the spelling.")
            return None

        if current_response.status_code == 401:
            print("Invalid API key or key not activated yet.")
            return None

        current_response.raise_for_status()

        current_data = current_response.json()

        # Forecast request
        forecast_response = requests.get(
            f"{BASE_URL}/forecast",
            params=parameters,
            timeout=15
        )

        if forecast_response.status_code == 401:
            print("API key is not authorized for forecast.")
            return None

        forecast_response.raise_for_status()

        forecast_data = forecast_response.json()

        result = {
            "current": current_data,
            "forecast": forecast_data
        }

        # Save results in cache
        cache[cache_key] = {
            "timestamp": current_time,
            "data": result
        }

        save_cache(cache)

        return result

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")

    except requests.exceptions.ConnectionError:
        print("Internet connection error.")

    except requests.exceptions.HTTPError as error:
        print("Weather API error:", error)

    except requests.exceptions.RequestException as error:
        print("Request failed:", error)

    except (ValueError, KeyError) as error:
        print("Error reading weather data:", error)

    return None


# Display weather information
def display_weather(data):

    current = data["current"]

    forecast = data["forecast"]

    city = current.get("name", "Unknown")

    country = current.get("sys", {}).get("country", "")

    main = current.get("main", {})

    weather = current.get("weather", [])

    description = "No description available"

    if weather:
        description = weather[0].get(
            "description",
            description
        )

    print("\n" + "=" * 40)

    print(f" WEATHER REPORT: {city}, {country}")

    print("=" * 40)

    print("Temperature :", main.get("temp", "N/A"), "°C")

    print("Feels Like  :", main.get("feels_like", "N/A"), "°C")

    print("Humidity    :", main.get("humidity", "N/A"), "%")

    print("Condition   :", description.title())

    print("\nSHORT WEATHER FORECAST")

    print("-" * 40)

    forecast_list = forecast.get("list", [])

    for item in forecast_list[:5]:

        date_time = item.get("dt_txt", "Unknown time")

        forecast_main = item.get("main", {})

        forecast_weather = item.get("weather", [])

        temperature = forecast_main.get("temp", "N/A")

        forecast_description = "N/A"

        if forecast_weather:
            forecast_description = forecast_weather[0].get(
                "description",
                "N/A"
            )

        print(
            date_time,
            "|",
            temperature,
            "°C |",
            forecast_description.title()
        )

    print("=" * 40)


# Main application
def main():

    print("===================================")

    print("         LIVE WEATHER APP")

    print("===================================")

    if not API_KEY:
        print("Please configure your API key in the .env file.")
        return

    while True:

        city = input(
            "\nEnter city name (or type exit): "
        ).strip()

        if city.lower() == "exit":

            print("Thank you for using Weather App!")

            break

        if not city:

            print("Please enter a city name.")

            continue

        weather_data = get_weather_data(city)

        if weather_data:

            display_weather(weather_data)


if __name__ == "__main__":
    main()
