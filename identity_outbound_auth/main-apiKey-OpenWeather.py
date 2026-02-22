#!/usr/bin/env python3
#
# pip3 install requests asyncio
#
import asyncio
import requests     
import os
import sys
import json
from bedrock_agentcore.identity.auth import requires_api_key

OPENWEATHER_API_KEY = None

# AgentCore Identity で登録した API KEY を取得
@requires_api_key(provider_name="OPENWEATHER_KEY")
async def need_api_key(*, api_key: str):
    global OPENWEATHER_API_KEY
    print("received api key for async func")
    OPENWEATHER_API_KEY = api_key

async def get_api_key():
    # APIキーを取得
    await need_api_key(api_key="")

# APIキーを非同期で取得
asyncio.run(get_api_key())
print(OPENWEATHER_API_KEY)

def get_weather(city="Seattle"):
    """
    Get current weather for a city using OpenWeather API
    
    Args:
        city: City name (default: Seattle)
    
    Returns:
        dict: Weather data
    """
    
    # OpenWeather API endpoint
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    # Request parameters
    params = {
        'q': city,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric',  # Use Celsius
        'lang': 'ja'  # Japanese language
    }
    
    try:
        # Make API request
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Extract relevant information
        weather_info = {
            'city': data['name'],
            'country': data['sys']['country'],
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'description': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed']
        }
        
        return weather_info
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: Invalid API key", file=sys.stderr)
        elif e.response.status_code == 404:
            print(f"Error: City '{city}' not found", file=sys.stderr)
        else:
            print(f"HTTP Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def display_weather(weather_info):
    """Display weather information in a readable format"""
    print(f"\n天気情報: {weather_info['city']}, {weather_info['country']}")
    print("=" * 50)
    print(f"気温: {weather_info['temperature']}°C")
    print(f"体感温度: {weather_info['feels_like']}°C")
    print(f"天気: {weather_info['description']}")
    print(f"湿度: {weather_info['humidity']}%")
    print(f"気圧: {weather_info['pressure']} hPa")
    print(f"風速: {weather_info['wind_speed']} m/s")
    print("=" * 50)


if __name__ == "__main__":
    # Get city from command line argument or use default
    city = sys.argv[1] if len(sys.argv) > 1 else "Seattle"
    
    # Get weather data
    weather = get_weather(city)
    
    # Display weather information
    display_weather(weather)
    
    # Also print JSON format
    print("\nJSON形式:")
    print(json.dumps(weather, indent=2, ensure_ascii=False))
