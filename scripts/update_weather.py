"""Fetch the 19-23 Oct 2026 forecast for the trip locations and write weather.json.
Run nightly by .github/workflows/weather.yml. Leaves weather.json untouched if the API fails."""
import datetime, json, sys, time, urllib.request, zoneinfo

LOCS = [("porth", 52.929, -4.131), ("bala", 52.911, -3.597), ("vyr", 52.76, -3.50), ("bedd", 53.012, -4.103)]
LAST_DAY = datetime.date(2026, 10, 23)
now = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/London"))
if now.date() > LAST_DAY:
    print("Trip is over, nothing to update.")
    sys.exit(0)

url = (
    "https://api.open-meteo.com/v1/forecast?latitude=" + ",".join(str(l[1]) for l in LOCS)
    + "&longitude=" + ",".join(str(l[2]) for l in LOCS)
    + "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,"
      "precipitation_probability_max,wind_gusts_10m_max"
      "&hourly=weather_code,temperature_2m,precipitation_probability,wind_gusts_10m&timezone=Europe%2FLondon"
      "&start_date=2026-10-19&end_date=2026-10-23"
)

data = None
for attempt in range(8):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
        if isinstance(data, list) and len(data) == len(LOCS):
            break
    except Exception as e:  # overloaded or network blip: wait and retry
        print("attempt", attempt + 1, "failed:", e)
    data = None
    time.sleep(15)

if data is None:
    print("Forecast unavailable, keeping the existing weather.json.")
    sys.exit(1)

d = {}
for (key, _, _), loc in zip(LOCS, data):
    x = loc["daily"]
    d[key] = {"c": x["weather_code"], "hi": x["temperature_2m_max"], "lo": x["temperature_2m_min"],
              "r": x["precipitation_sum"], "p": x["precipitation_probability_max"], "g": x["wind_gusts_10m_max"]}
    assert all(len(v) == 5 for v in d[key].values()), "unexpected forecast length"
    h = loc["hourly"]
    d[key]["h"] = {"c": h["weather_code"], "t": h["temperature_2m"], "p": h["precipitation_probability"], "g": h["wind_gusts_10m"]}
    assert all(len(v) == 120 for v in d[key]["h"].values()), "unexpected hourly length"

with open("weather.json", "w", encoding="utf-8") as f:
    json.dump({"stamp": now.strftime("%d/%m %H:%M"), "d": d}, f, ensure_ascii=False, indent=1)
print("weather.json updated", now.isoformat())
