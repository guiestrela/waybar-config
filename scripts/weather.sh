#!/bin/bash
# Weather Script for Waybar
# Returns JSON with weather info
# Uses wttr.in (free, no API key required)

# CONFIG: Set your location
LOCATION=""

# Default to IP-based location if not set
if [ -z "$LOCATION" ]; then
    weather=$(curl -s "wttr.in/?format=j1" 2>/dev/null)
else
    weather=$(curl -s "wttr.in/${LOCATION}?format=j1" 2>/dev/null)
fi

if [ -z "$weather" ]; then
    echo "{\"text\": \"N/A\", \"tooltip\": \"Weather: Unavailable\"}"
    exit 0
fi

# Parse weather data
condition=$(echo "$weather" | jq -r '.current_condition[0].weatherDesc[0].value')
temp_c=$(echo "$weather" | jq -r '.current_condition[0].temp_C')
humidity=$(echo "$weather" | jq -r '.current_condition[0].humidity')
feels_like=$(echo "$weather" | jq -r '.current_condition[0].FeelsLikeC')

# Weather icon mapping
case $condition in
    *"Sunny"*|*"Clear"*) icon="☀️" ;;
    *"Cloudy"*|*"Overcast"*) icon="☁️" ;;
    *"Partly cloudy"*) icon="⛅" ;;
    *"Mist"*|*"Fog"*) icon="🌫️" ;;
    *"Rain"*|*"Drizzle"*) icon="🌧️" ;;
    *"Snow"*|*"Sleet"*) icon="❄️" ;;
    *"Thunder"*) icon="⛈️" ;;
    *) icon="🌡️" ;;
esac

echo "{\"text\": \"${icon} ${temp_c}°C\", \"tooltip\": \"${condition}\nTemp: ${temp_c}°C (Feels ${feels_like}°C)\nHumidity: ${humidity}%\"}"
