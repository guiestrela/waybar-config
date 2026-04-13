#!/usr/bin/env python3
import json
import os
from datetime import datetime
from urllib.request import urlopen, Request
import ssl

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "weather_api.conf")
API_KEY_ENV_VAR = "OPENWEATHER_API_KEY"
UNITS = "metric"

CITY = "Brasilia"
COUNTRY = "BR"

tooltip_icons = {
    "01d": "☀️",
    "01n": "🌕",
    "02d": "⛅",
    "02n": "☁️",
    "03d": "☁️",
    "03n": "☁️",
    "04d": "☁️",
    "04n": "☁️",
    "09d": "🌧️",
    "09n": "🌧️",
    "10d": "🌦️",
    "10n": "🌧️",
    "11d": "⛈️",
    "11n": "⛈️",
    "13d": "🌨️",
    "13n": "🌨️",
    "50d": "🌫️",
    "50n": "🌫️",
}

module_icons = {
    "01d": "󰖙",  # clear day
    "01n": "󰖔",  # clear night
    "02d": "󰖕",  # few clouds day
    "02n": "󰼱",  # few clouds night
    "03d": "󰖐",  # scattered clouds
    "03n": "󰖐",
    "04d": "󰖐",  # broken clouds
    "04n": "󰖐",
    "09d": "󰖖",  # shower rain
    "09n": "󰖖",
    "10d": "󰖗",  # rain day
    "10n": "󰖗",  # rain night
    "11d": "󰖓",  # thunderstorm
    "11n": "󰖓",
    "13d": "󰖘",  # snow
    "13n": "󰖘",
    "50d": "󰖑",  # mist
    "50n": "󰖑",
}


def load_api_key():
    env_api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if env_api_key:
        return env_api_key
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def fetch_json(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=10, context=ctx) as response:
        return json.loads(response.read().decode())


def get_weather():
    api_key = load_api_key()
    if not api_key:
        return (
            "weather",
            "Configure a chave da API em weather_api.conf ou OPENWEATHER_API_KEY",
        )

    try:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY},{COUNTRY}&appid={api_key}&units={UNITS}&lang=en"
        r = fetch_json(weather_url)
    except Exception as e:
        return "weather", f"Weather unavailable: {e}"

    if "main" not in r:
        return "weather", "Weather unavailable"

    temp = round(r["main"]["temp"])
    desc = r["weather"][0]["description"]
    icon_code = r["weather"][0]["icon"]
    city = r["name"]

    tooltip_icon = tooltip_icons.get(icon_code, "🌡️")
    module_icon = module_icons.get(icon_code, "󰔏")

    try:
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY},{COUNTRY}&appid={api_key}&units={UNITS}&lang=en"
        fc = fetch_json(forecast_url)["list"]
    except:
        fc = []

    lines = []
    seen = set()
    for entry in fc:
        date = entry["dt_txt"][:10]
        if date in seen or len(lines) >= 6:
            continue
        if "12:00" in entry["dt_txt"] or "15:00" in entry["dt_txt"]:
            seen.add(date)
            day = datetime.fromtimestamp(entry["dt"]).strftime("%a")
            t = round(entry["main"]["temp"])
            i = tooltip_icons.get(entry["weather"][0]["icon"], "🌡️")
            lines.append(f"{i}  {day} {t}°C")

    tooltip = f"<big><b>{city}</b></big>\n"
    tooltip += f"{tooltip_icon}  {temp}°C • {desc.capitalize()}\n"
    tooltip += f"💧 {r['main']['humidity']}%   💨 {r.get('wind', {}).get('speed', '?')} m/s\n\n"
    tooltip += "Next days:\n" + "\n".join(lines)

    return f"<b>{module_icon}  {temp}°C</b>", tooltip


text, tooltip = get_weather()
print(json.dumps({"text": text, "tooltip": tooltip, "class": "weather"}))
