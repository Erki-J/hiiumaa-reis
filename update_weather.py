#!/usr/bin/env python3
"""Fetch weather and inject into hiiumaa.html / index.html."""

import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

UA = "hiiumaa-reis/1.0 github.com/Erki-J/hiiumaa-reis"
TZ = ZoneInfo("Europe/Tallinn")
ROOT = Path(__file__).parent

CONFIG = [
    (1, "2026-07-16", 58.7597, 22.8075, "Sääretirp"),
    (2, "2026-07-17", 59.0396, 22.6871, "Tõrvanina"),
    (3, "2026-07-18", 59.0396, 22.6871, "Tõrvanina"),
    (4, "2026-07-19", 59.0396, 22.6871, "Tõrvanina"),
    (5, "2026-07-20", 58.908368, 22.133048, "Kaleste"),
    (6, "2026-07-21", 58.908368, 22.133048, "Kaleste"),
]

ICONS = {
    "sun": '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="7" fill="#fbbf24"/><g stroke="#fbbf24" stroke-width="2" stroke-linecap="round"><line x1="16" y1="3" x2="16" y2="7"/><line x1="16" y1="25" x2="16" y2="29"/><line x1="3" y1="16" x2="7" y2="16"/><line x1="25" y1="16" x2="29" y2="16"/><line x1="6.8" y1="6.8" x2="9.6" y2="9.6"/><line x1="22.4" y1="22.4" x2="25.2" y2="25.2"/><line x1="6.8" y1="25.2" x2="9.6" y2="22.4"/><line x1="22.4" y1="9.6" x2="25.2" y2="6.8"/></g></svg>',
    "partly": '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><circle cx="12" cy="13" r="6" fill="#fbbf24"/><path d="M10 22h14a6 6 0 0 0 .4-12 7.5 7.5 0 0 0-14.6 1.8A4.5 4.5 0 0 0 10 22z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1"/></svg>',
    "cloudy": '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M9 22h15a5.5 5.5 0 0 0 .5-11 6.5 6.5 0 0 0-12.6 1.6A4 4 0 0 0 9 22z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1"/></svg>',
    "rain": '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M9 20h15a5.5 5.5 0 0 0 .5-11 6.5 6.5 0 0 0-12.6 1.6A4 4 0 0 0 9 20z" fill="#cbd5e1" stroke="#94a3b8" stroke-width="1"/><g stroke="#38bdf8" stroke-width="2" stroke-linecap="round"><line x1="12" y1="23" x2="10" y2="27"/><line x1="18" y1="23" x2="16" y2="27"/><line x1="24" y1="23" x2="22" y2="27"/></g></svg>',
    "moon": '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M18 6a10 10 0 1 0 8 14.5A8 8 0 0 1 18 6z" fill="#94a3b8"/></svg>',
    "moon_partly": '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M17 7a9 9 0 1 0 7 12.5A7 7 0 0 1 17 7z" fill="#94a3b8"/><path d="M20 20h8a4 4 0 0 0 .2-8 5 5 0 0 0-9.5 1.2A3 3 0 0 0 20 20z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1"/></svg>',
}


def icon_html(kind, period):
    if period == "evening":
        if kind == "sun":
            return ICONS["moon"]
        if kind in ("partly", "cloudy"):
            return ICONS["moon_partly"]
    return ICONS.get(kind, ICONS["cloudy"])


def icon_met(code):
    if not code:
        return "cloudy"
    c = code.lower()
    if any(x in c for x in ("thunder", "rain", "showers", "drizzle", "snow", "sleet")):
        return "rain"
    if c.startswith("clearsky"):
        return "sun"
    if "fair" in c or "partlycloudy" in c:
        return "partly"
    return "cloudy"


def icon_wmo(code):
    if code == 0:
        return "sun"
    if code in (1, 2):
        return "partly"
    if code == 3:
        return "cloudy"
    if code in range(45, 100):
        return "rain"
    return "cloudy"


def fetch_metno(lat, lon):
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["properties"]["timeseries"]


def fetch_openmeteo(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&timezone=Europe%2FTallinn"
        "&daily=temperature_2m_max,temperature_2m_min"
        "&hourly=temperature_2m,weather_code&forecast_days=16"
    )
    with urllib.request.urlopen(url) as r:
        return json.load(r)


def met_symbol(data):
    for key in ("next_1_hours", "next_6_hours", "next_12_hours"):
        if key in data and "summary" in data[key]:
            return data[key]["summary"].get("symbol_code")
    return None


def summarize_metno(ts, date_str):
    temps = []
    periods = {"morning": None, "noon": None, "evening": None}
    for entry in ts:
        t = datetime.fromisoformat(entry["time"].replace("Z", "+00:00")).astimezone(TZ)
        if t.strftime("%Y-%m-%d") != date_str:
            continue
        temps.append(entry["data"]["instant"]["details"]["air_temperature"])
        h = t.hour
        p = "morning" if 6 <= h < 12 else "noon" if 12 <= h < 18 else "evening" if 18 <= h < 24 else None
        if p and periods[p] is None:
            periods[p] = icon_met(met_symbol(entry["data"]))
    if not temps:
        return None
    for p in periods:
        if periods[p] is None:
            periods[p] = "cloudy"
    return {"max": round(max(temps)), "min": round(min(temps)), **periods, "source": "yr.no"}


def summarize_openmeteo(data, date_str):
    daily = data["daily"]
    if date_str not in daily["time"]:
        return None
    i = daily["time"].index(date_str)
    max_t = daily["temperature_2m_max"][i]
    min_t = daily["temperature_2m_min"][i]
    hourly_t = []
    periods = {"morning": None, "noon": None, "evening": None}
    for t, code, temp in zip(data["hourly"]["time"], data["hourly"]["weather_code"], data["hourly"]["temperature_2m"]):
        if not t.startswith(date_str):
            continue
        if temp is not None:
            hourly_t.append(temp)
        h = int(t[11:13])
        p = "morning" if 6 <= h < 12 else "noon" if 12 <= h < 18 else "evening" if 18 <= h < 24 else None
        if p and periods[p] is None:
            periods[p] = icon_wmo(code)
    if max_t is None and hourly_t:
        max_t = max(hourly_t)
    if min_t is None and hourly_t:
        min_t = min(hourly_t)
    if max_t is None or min_t is None:
        return None
    for p in periods:
        if periods[p] is None:
            periods[p] = "cloudy"
    return {"max": round(max_t), "min": round(min_t), **periods, "source": "open-meteo"}


def fetch_weather():
    met_cache, om_cache = {}, {}
    result = {}
    for day, date, lat, lon, place in CONFIG:
        key = (lat, lon)
        if key not in met_cache:
            met_cache[key] = fetch_metno(lat, lon)
        if key not in om_cache:
            om_cache[key] = fetch_openmeteo(lat, lon)
        w = summarize_metno(met_cache[key], date) or summarize_openmeteo(om_cache[key], date)
        w["place"] = place
        result[day] = w
    return result


def weather_block(day, w):
    labels = [("morning", "Hommik"), ("noon", "Lõuna"), ("evening", "Õhtu")]
    slots = "".join(
        f'<div class="weather-slot">{icon_html(w[p], p)}<span class="weather-label">{label}</span></div>'
        for p, label in labels
    )
    src = "yr.no" if w["source"] == "yr.no" else "open-meteo.com"
    return (
        f'        <div class="day-weather" data-day="{day}">\n'
        f'          <div class="weather-row">{slots}</div>\n'
        f'          <div class="weather-temp"><strong>{w["max"]}°</strong> / {w["min"]}°</div>\n'
        f'          <button type="button" class="weather-refresh" title="Uuenda ilma kõigil päevadel">{src}</button>\n'
        f"        </div>\n"
    )


def insert_weather(header_inner, block):
    if re.search(r'<div class="day-stats">', header_inner):
        return re.sub(
            r'(<div class="day-title">[\s\S]*?</div>\n)(\s*<div class="day-stats">)',
            r"\1" + block + r"\2",
            header_inner,
            count=1,
        )
    return re.sub(
        r'(<div class="day-title">[\s\S]*?</div>\n)(\s*</div>)',
        r"\1" + block + r"\2",
        header_inner,
        count=1,
    )


WEATHER_CSS = """
    .day-header {
      flex-direction: column;
      align-items: stretch;
      gap: 0.75rem;
    }

    .day-header-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .day-weather {
      display: flex;
      align-items: center;
      gap: 0.75rem 1rem;
      flex-wrap: wrap;
      padding-top: 0.25rem;
      border-top: 1px solid var(--border);
    }

    .weather-place {
      font-size: 0.75rem;
      color: var(--muted);
      min-width: 4.5rem;
    }

    .weather-row {
      display: flex;
      gap: 0.75rem;
      flex: 1;
    }

    .weather-slot {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.15rem;
      min-width: 3rem;
    }

    .weather-label {
      font-size: 0.65rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }

    .wicon {
      width: 2rem;
      height: 2rem;
    }

    .weather-temp {
      font-size: 0.95rem;
      white-space: nowrap;
    }

    .weather-temp strong {
      color: #ea580c;
      font-weight: 700;
    }

    .weather-src {
      font-size: 0.65rem;
      color: var(--muted);
      margin-left: auto;
    }

    @media (max-width: 540px) {
      .day-weather {
        flex-direction: column;
        align-items: flex-start;
      }

      .weather-src {
        margin-left: 0;
      }
    }
"""


def strip_weather(header_inner):
    while True:
        new = re.sub(
            r'\s*<div class="day-weather"[^>]*>[\s\S]*?(?:</span>|</button>)\s*</div>',
            "",
            header_inner,
            count=1,
        )
        if new == header_inner:
            break
        header_inner = new
    return re.sub(
        r'\s*<div class="weather-temp">.*?</div>\s*(?:<span class="weather-src">[^<]*</span>|<button type="button" class="weather-refresh"[^>]*>[^<]*</button>)\s*</div>',
        "",
        header_inner,
        flags=re.DOTALL,
    )


def patch_html(path, weather):
    html = path.read_text(encoding="utf-8")

    if ".day-weather" not in html:
        html = html.replace(
            "    .day-header {\n      display: flex;\n      align-items: center;\n      justify-content: space-between;\n      gap: 1rem;\n      padding: 1rem 1.25rem;\n      background: var(--sea-light);\n      border-bottom: 1px solid var(--border);\n    }",
            "    .day-header {\n      display: flex;\n      flex-direction: column;\n      align-items: stretch;\n      gap: 0.75rem;\n      padding: 1rem 1.25rem;\n      background: var(--sea-light);\n      border-bottom: 1px solid var(--border);\n    }\n\n    .day-header-top {\n      display: flex;\n      align-items: center;\n      justify-content: space-between;\n      gap: 1rem;\n    }" + WEATHER_CSS,
        )

    for day in range(1, 7):
        block = weather_block(day, weather[day])
        pattern = rf'(<!-- Päev {day} -->.*?<div class="day-header">\n)(.*?)(      </div>\n      <div class="day-body">)'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            raise SystemExit(f"Could not find day {day} header")
        header_inner = match.group(2)
        header_inner = strip_weather(header_inner)
        if "day-header-top" not in header_inner:
            if 'class="day-stats"' in header_inner:
                header_inner = re.sub(
                    r'(<div class="day-title">.*?</div>\n)(        <div class="day-stats">.*?</div>\n)',
                    r'        <div class="day-header-top">\n          \1          \2        </div>\n',
                    header_inner,
                    count=1,
                    flags=re.DOTALL,
                )
            else:
                header_inner = re.sub(
                    r'(<div class="day-title">.*?</div>\n)',
                    r'        <div class="day-header-top">\n          \1        </div>\n',
                    header_inner,
                    count=1,
                    flags=re.DOTALL,
                )

        header_inner = strip_weather(header_inner)
        header_inner = insert_weather(header_inner, block)
        html = html[: match.start(2)] + header_inner + html[match.end(2) :]

    path.write_text(html, encoding="utf-8")


def main():
    weather = fetch_weather()
    (ROOT / "weather.json").write_text(json.dumps(weather, indent=2), encoding="utf-8")
    for name in ("hiiumaa.html", "index.html"):
        patch_html(ROOT / name, weather)
    print("Updated weather for", len(weather), "days")


if __name__ == "__main__":
    main()
