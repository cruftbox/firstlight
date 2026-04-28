import requests
import time
from datetime import datetime
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


def _get_air_quality(lat: float, lon: float) -> int | None:
    try:
        resp = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={"latitude": lat, "longitude": lon, "current": "us_aqi"},
            timeout=10,
        )
        resp.raise_for_status()
        aqi = resp.json().get("current", {}).get("us_aqi")
        return int(aqi) if aqi is not None else None
    except Exception:
        return None


def _aqi_label(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


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
        stale = entry["data"] if entry else None

    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weathercode,windspeed_10m",
        "hourly": "temperature_2m,weathercode",
        "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum",
        "temperature_unit": temp_unit,
        "timezone": "auto",
        "forecast_days": 4,
    }
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception:
        return stale

    current = raw.get("current", {})
    code = current.get("weathercode", 0)
    temp = current.get("temperature_2m")
    wind = current.get("windspeed_10m")
    daily = raw.get("daily", {})
    high = daily.get("temperature_2m_max", [None])[0]
    low = daily.get("temperature_2m_min", [None])[0]

    # Sunrise / sunset — Open-Meteo returns local time as "YYYY-MM-DDTHH:MM"
    def _fmt_time(iso_str):
        if not iso_str:
            return None
        try:
            return datetime.fromisoformat(iso_str).strftime("%-I:%M %p")
        except Exception:
            return None

    sunrise = _fmt_time((daily.get("sunrise") or [None])[0])
    sunset = _fmt_time((daily.get("sunset") or [None])[0])

    # Rain in the next 3 days (indices 1-3 of daily arrays)
    daily_times = daily.get("time", [])
    precip = daily.get("precipitation_sum", [])
    rain_days = []
    for i in range(1, min(4, len(daily_times))):
        if i < len(precip) and precip[i] is not None and precip[i] >= 1.0:
            try:
                day_name = datetime.strptime(daily_times[i], "%Y-%m-%d").strftime("%A")
                rain_days.append(day_name)
            except Exception:
                pass

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

    aqi = _get_air_quality(lat, lon)

    result = {
        "condition": WMO_CODES.get(code, "Unknown"),
        "temp": round(temp) if temp is not None else None,
        "high": round(high) if high is not None else None,
        "low": round(low) if low is not None else None,
        "wind": round(wind) if wind is not None else None,
        "units": units,
        "hourly": hourly_strip,
        "sunrise": sunrise,
        "sunset": sunset,
        "rain_days": rain_days,
        "aqi": aqi,
        "aqi_label": _aqi_label(aqi) if aqi is not None else None,
    }

    with _cache_lock:
        _cache[cache_key] = {"ts": time.time(), "data": result}

    return result
