(function () {
  var UA = "hiiumaa-reis/1.0 github.com/Erki-J/hiiumaa-reis";

  var CONFIG = [
    { day: 1, date: "2026-07-16", lat: 58.7597, lon: 22.8075 },
    { day: 2, date: "2026-07-17", lat: 59.0396, lon: 22.6871 },
    { day: 3, date: "2026-07-18", lat: 59.0396, lon: 22.6871 },
    { day: 4, date: "2026-07-19", lat: 59.0396, lon: 22.6871 },
    { day: 5, date: "2026-07-20", lat: 58.908368, lon: 22.133048 },
    { day: 6, date: "2026-07-21", lat: 58.908368, lon: 22.133048 },
  ];

  var ICONS = {
    sun: '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="7" fill="#fbbf24"/><g stroke="#fbbf24" stroke-width="2" stroke-linecap="round"><line x1="16" y1="3" x2="16" y2="7"/><line x1="16" y1="25" x2="16" y2="29"/><line x1="3" y1="16" x2="7" y2="16"/><line x1="25" y1="16" x2="29" y2="16"/><line x1="6.8" y1="6.8" x2="9.6" y2="9.6"/><line x1="22.4" y1="22.4" x2="25.2" y2="25.2"/><line x1="6.8" y1="25.2" x2="9.6" y2="22.4"/><line x1="22.4" y1="9.6" x2="25.2" y2="6.8"/></g></svg>',
    partly: '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><circle cx="12" cy="13" r="6" fill="#fbbf24"/><path d="M10 22h14a6 6 0 0 0 .4-12 7.5 7.5 0 0 0-14.6 1.8A4.5 4.5 0 0 0 10 22z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1"/></svg>',
    cloudy: '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M9 22h15a5.5 5.5 0 0 0 .5-11 6.5 6.5 0 0 0-12.6 1.6A4 4 0 0 0 9 22z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1"/></svg>',
    rain: '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M9 20h15a5.5 5.5 0 0 0 .5-11 6.5 6.5 0 0 0-12.6 1.6A4 4 0 0 0 9 20z" fill="#cbd5e1" stroke="#94a3b8" stroke-width="1"/><g stroke="#38bdf8" stroke-width="2" stroke-linecap="round"><line x1="12" y1="23" x2="10" y2="27"/><line x1="18" y1="23" x2="16" y2="27"/><line x1="24" y1="23" x2="22" y2="27"/></g></svg>',
    moon: '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M18 6a10 10 0 1 0 8 14.5A8 8 0 0 1 18 6z" fill="#94a3b8"/></svg>',
    moon_partly: '<svg class="wicon" viewBox="0 0 32 32" aria-hidden="true"><path d="M17 7a9 9 0 1 0 7 12.5A7 7 0 0 1 17 7z" fill="#94a3b8"/><path d="M20 20h8a4 4 0 0 0 .2-8 5 5 0 0 0-9.5 1.2A3 3 0 0 0 20 20z" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1"/></svg>',
  };

  var PERIODS = [
    ["morning", "Hommik"],
    ["noon", "Lõuna"],
    ["evening", "Õhtu"],
  ];

  var updating = false;
  var CACHE_KEY = "hiiumaa_weather_cache_v1";

  function iconHtml(kind, period) {
    if (period === "evening") {
      if (kind === "sun") return ICONS.moon;
      if (kind === "partly" || kind === "cloudy") return ICONS.moon_partly;
    }
    return ICONS[kind] || ICONS.cloudy;
  }

  function iconMet(code) {
    if (!code) return "cloudy";
    var c = code.toLowerCase();
    if (/thunder|rain|showers|drizzle|snow|sleet/.test(c)) return "rain";
    if (c.indexOf("clearsky") === 0) return "sun";
    if (c.indexOf("fair") !== -1 || c.indexOf("partlycloudy") !== -1) return "partly";
    return "cloudy";
  }

  function iconWmo(code) {
    if (code === 0) return "sun";
    if (code === 1 || code === 2) return "partly";
    if (code === 3) return "cloudy";
    if (code >= 45 && code < 100) return "rain";
    return "cloudy";
  }

  function periodForHour(h) {
    if (h >= 6 && h < 12) return "morning";
    if (h >= 12 && h < 18) return "noon";
    if (h >= 18 && h < 24) return "evening";
    return null;
  }

  function metSymbol(data) {
    var keys = ["next_1_hours", "next_6_hours", "next_12_hours"];
    for (var i = 0; i < keys.length; i++) {
      var block = data[keys[i]];
      if (block && block.summary) return block.summary.symbol_code;
    }
    return null;
  }

  function fetchMetno(lat, lon) {
    var url = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=" + lat + "&lon=" + lon;
    return fetch(url, { headers: { "User-Agent": UA } })
      .then(function (r) {
        if (!r.ok) throw new Error("yr.no " + r.status);
        return r.json();
      })
      .then(function (data) {
        return data.properties.timeseries;
      });
  }

  function fetchOpenMeteo(lat, lon) {
    var url =
      "https://api.open-meteo.com/v1/forecast?latitude=" +
      lat +
      "&longitude=" +
      lon +
      "&timezone=Europe%2FTallinn&daily=temperature_2m_max,temperature_2m_min&hourly=temperature_2m,weather_code&forecast_days=16";
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error("open-meteo " + r.status);
      return r.json();
    });
  }

  function tallinnParts(iso) {
    var str = new Date(iso).toLocaleString("sv-SE", { timeZone: "Europe/Tallinn" });
    var parts = str.split(/[- :]/);
    return {
      date: parts[0] + "-" + parts[1] + "-" + parts[2],
      hour: parseInt(parts[3], 10),
    };
  }

  function summarizeMetno(ts, dateStr) {
    var temps = [];
    var periods = { morning: null, noon: null, evening: null };
    for (var i = 0; i < ts.length; i++) {
      var entry = ts[i];
      var local = tallinnParts(entry.time);
      if (local.date !== dateStr) continue;
      temps.push(entry.data.instant.details.air_temperature);
      var p = periodForHour(local.hour);
      if (p && periods[p] === null) periods[p] = iconMet(metSymbol(entry.data));
    }
    if (!temps.length) return null;
    PERIODS.forEach(function (pair) {
      if (!periods[pair[0]]) periods[pair[0]] = "cloudy";
    });
    return {
      max: Math.round(Math.max.apply(null, temps)),
      min: Math.round(Math.min.apply(null, temps)),
      morning: periods.morning,
      noon: periods.noon,
      evening: periods.evening,
      source: "yr.no",
    };
  }

  function summarizeOpenMeteo(data, dateStr) {
    var daily = data.daily;
    var idx = daily.time.indexOf(dateStr);
    if (idx === -1) return null;
    var maxT = daily.temperature_2m_max[idx];
    var minT = daily.temperature_2m_min[idx];
    var hourlyT = [];
    var periods = { morning: null, noon: null, evening: null };
    for (var i = 0; i < data.hourly.time.length; i++) {
      var t = data.hourly.time[i];
      if (t.indexOf(dateStr) !== 0) continue;
      var temp = data.hourly.temperature_2m[i];
      if (temp !== null) hourlyT.push(temp);
      var p = periodForHour(parseInt(t.slice(11, 13), 10));
      if (p && periods[p] === null) periods[p] = iconWmo(data.hourly.weather_code[i]);
    }
    if (maxT === null && hourlyT.length) maxT = Math.max.apply(null, hourlyT);
    if (minT === null && hourlyT.length) minT = Math.min.apply(null, hourlyT);
    if (maxT === null || minT === null) return null;
    PERIODS.forEach(function (pair) {
      if (!periods[pair[0]]) periods[pair[0]] = "cloudy";
    });
    return {
      max: Math.round(maxT),
      min: Math.round(minT),
      morning: periods.morning,
      noon: periods.noon,
      evening: periods.evening,
      source: "open-meteo",
    };
  }

  function renderWeatherRow(w) {
    return PERIODS.map(function (pair) {
      return (
        '<div class="weather-slot">' +
        iconHtml(w[pair[0]], pair[0]) +
        '<span class="weather-label">' +
        pair[1] +
        "</span></div>"
      );
    }).join("");
  }

  function sourceLabel(source) {
    return source === "yr.no" ? "yr.no" : "open-meteo.com";
  }

  function applyWeather(el, w) {
    var row = el.querySelector(".weather-row");
    var temp = el.querySelector(".weather-temp");
    var btn = el.querySelector(".weather-refresh");
    if (row) row.innerHTML = renderWeatherRow(w);
    if (temp) temp.innerHTML = "<strong>" + w.max + "°</strong> / " + w.min + "°";
    if (btn) btn.textContent = sourceLabel(w.source);
    el.classList.remove("is-updating");
  }

  function setUpdating(all, on) {
    all.forEach(function (el) {
      el.classList.toggle("is-updating", on);
      var btn = el.querySelector(".weather-refresh");
      if (btn) {
        btn.disabled = on;
        if (on) btn.textContent = "…";
      }
    });
  }

  function fetchDayWeather(cfg, metCache, omCache) {
    var key = cfg.lat + "," + cfg.lon;
    var metPromise = metCache[key]
      ? Promise.resolve(metCache[key])
      : fetchMetno(cfg.lat, cfg.lon)
          .then(function (ts) {
            metCache[key] = ts;
            return ts;
          })
          .catch(function () {
            metCache[key] = null;
            return null;
          });
    var omPromise = omCache[key]
      ? Promise.resolve(omCache[key])
      : fetchOpenMeteo(cfg.lat, cfg.lon).then(function (data) {
          omCache[key] = data;
          return data;
        });

    return Promise.all([metPromise, omPromise]).then(function (results) {
      var met = results[0] ? summarizeMetno(results[0], cfg.date) : null;
      if (met) return met;
      return summarizeOpenMeteo(results[1], cfg.date);
    });
  }

  function saveWeatherCache(results) {
    try {
      if (!window.sessionStorage) return;
      var data = {};
      results.forEach(function (w, i) {
        data[CONFIG[i].day] = w;
      });
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch (_) {
      // Ignore storage access issues.
    }
  }

  function loadWeatherCache() {
    try {
      if (!window.sessionStorage) return false;
      var raw = sessionStorage.getItem(CACHE_KEY);
      if (!raw) return false;
      var data = JSON.parse(raw);
      CONFIG.forEach(function (cfg) {
        var w = data[cfg.day];
        if (!w) return;
        var el = document.querySelector('#reisiplaan .day-weather[data-day="' + cfg.day + '"]');
        if (el) applyWeather(el, w);
      });
      return true;
    } catch (_) {
      return false;
    }
  }

  function refreshAllWeather() {
    if (updating) return;
    var blocks = document.querySelectorAll("#reisiplaan .day-weather[data-day]");
    if (!blocks.length) return;

    updating = true;
    setUpdating(Array.prototype.slice.call(blocks), true);

    var metCache = {};
    var omCache = {};
    var promises = CONFIG.map(function (cfg) {
      return fetchDayWeather(cfg, metCache, omCache).then(function (w) {
        if (!w) throw new Error("no data for day " + cfg.day);
        var el = document.querySelector('#reisiplaan .day-weather[data-day="' + cfg.day + '"]');
        if (el) applyWeather(el, w);
        return w;
      });
    });

    Promise.all(promises)
      .then(function (results) {
        saveWeatherCache(results);
      })
      .catch(function () {
        blocks.forEach(function (el) {
          var btn = el.querySelector(".weather-refresh");
          el.classList.remove("is-updating");
          if (btn) {
            btn.disabled = false;
            if (btn.textContent === "…") btn.textContent = "viga";
          }
        });
      })
      .finally(function () {
        updating = false;
        blocks.forEach(function (el) {
          var btn = el.querySelector(".weather-refresh");
          if (btn) btn.disabled = false;
        });
      });
  }

  function initWeather() {
    loadWeatherCache();
    refreshAllWeather();
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".weather-refresh");
    if (!btn) return;
    e.preventDefault();
    refreshAllWeather();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWeather, { once: true });
  } else {
    initWeather();
  }
})();
