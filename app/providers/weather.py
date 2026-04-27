import requests
import time
from threading import Lock

_cache: dict = {}
_cache_lock = Lock()
CACHE_TTL = 1800  # 30 minutes

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def geocode(city: str) -> dict | None:
    """Returns {"name", "lat", "lon", "country"} or None if not found."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        resp = requests.get(url, params={"name": city, "count": 1, "format": "json"}, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception:
        return None
    if not results:
        return None
    r = results[0]
    return {
        "name": r["name"],
        "lat": r["latitude"],
        "lon": r["longitude"],
        "country": r.get("country", ""),
    }


def get_forecast(lat: float, lon: float, units: str = "imperial") -> dict | None:
    """Returns weather dict or None on failure. Cached for 30 minutes."""
    cache_key = (lat, lon, units)
    with _cache_lock:
        entry = _cache.get(cache_key)
        if entry and time.time() - entry["ts"] < CACHE_TTL:
            return entry["data"]

    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weathercode,windspeed_10m",
        "hourly": "temperature_2m,weathercode",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": temp_unit,
        "timezone": "auto",
        "forecast_days": 1,
    }
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception:
        return None

    current = raw.get("current", {})
    code = current.get("weathercode", 0)
    temp = current.get("temperature_2m")
    wind = current.get("windspeed_10m")
    daily = raw.get("daily", {})
    high = daily.get("temperature_2m_max", [None])[0]
    low = daily.get("temperature_2m_min", [None])[0]

    hourly_times = raw.get("hourly", {}).get("time", [])
    hourly_temps = raw.get("hourly", {}).get("temperature_2m", [])
    target_hours = [6, 9, 12, 15, 18]
    hourly_strip = []
    for h in target_hours:
        suffix = f"T{h:02d}:00"
        for i, t in enumerate(hourly_times):
            if t.endswith(suffix):
                hourly_strip.append({"hour": h, "temp": round(hourly_temps[i])})
                break

    result = {
        "condition": WMO_CODES.get(code, "Unknown"),
        "temp": round(temp) if temp is not None else None,
        "high": round(high) if high is not None else None,
        "low": round(low) if low is not None else None,
        "wind": round(wind) if wind is not None else None,
        "units": units,
        "hourly": hourly_strip,
    }

    with _cache_lock:
        _cache[cache_key] = {"ts": time.time(), "data": result}

    return result
