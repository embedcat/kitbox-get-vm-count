const STATS_MAX_AGE_MS = 3 * 60 * 60 * 1000
const SERVERS_MAX_AGE_MS = 15 * 60 * 1000
const HISTORY_WINDOW_MS = 24 * 60 * 60 * 1000
const HISTORY_BUCKET_MS = 30 * 60 * 1000
const MSK_DATE_FORMAT = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Moscow", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23"
})
const MSK_TIME_FORMAT = new Intl.DateTimeFormat("en-GB", {timeZone: "Europe/Moscow", hour: "2-digit", minute: "2-digit", hourCycle: "h23"})

function onReady() {
    fetch('./data/data.json', {cache: "no-store"})
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            return response.json()
        })
        .then((data) => {
            document.getElementById("counter").textContent = String(data["counter"])
            var list = document.getElementById("devices")
            list.textContent = ""
            for (const device of data["device_count"]) {
                var li = document.createElement("li")
                li.appendChild(document.createTextNode(device))
                li.setAttribute("class", "device-item")
                list.appendChild(li)
            }
            showUpdated("updated", data, STATS_MAX_AGE_MS)
        })
        .catch((error) => {
            document.getElementById("counter").textContent = "No data"
            showError("devices", `data.json unavailable: ${error.message}`)
            showUpdated("updated", null)
        });
    fetch('./data/server_status.json', {cache: "no-store"})
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            return response.json()
        })
        .then((data) => {
            var list = document.getElementById("servers")
            list.textContent = ""
            var entries = [data["services"], data["mqtt"]]
            var lastFailures = []
            for (const entry of entries) {
                var li = document.createElement("li")
                li.appendChild(document.createTextNode(`${entry["name"]}: ${entry["ok"] ? "OK" : "FAILURE"}`))
                li.setAttribute("class", entry["ok"] ? "servers-item" : "failure")
                if (entry["detail"]) {
                    li.setAttribute("title", entry["detail"])
                }
                list.appendChild(li)
                if (entry["last_failure"]) {
                    lastFailures.push(`${entry["name"]}: ${entry["last_failure"]}`)
                }
            }
            showUpdated("updated-servers", data, SERVERS_MAX_AGE_MS)
            document.getElementById("last-failure").textContent = lastFailures.length ? "Last failure — " + lastFailures.join(", ") : ""
            showUptime(data)
        })
        .catch((error) => {
            showError("servers", `server_status.json unavailable: ${error.message}`)
            showUpdated("updated-servers", null)
            document.getElementById("last-failure").textContent = ""
            showUptime(null)
        });
}

function showUpdated(elementId, data, maxAgeMs) {
    var element = document.getElementById(elementId)
    if (!data) {
        element.textContent = ""
        element.classList.remove("stale")
        return
    }
    var age = Date.now() - Date.parse(data["updated_ts"])
    var stale = !(age <= maxAgeMs)
    element.textContent = String(data["updated_datetime"]) + (stale ? " — stale" : "")
    element.classList.toggle("stale", stale)
}

function buildBuckets(history, key, nowMs) {
    var count = HISTORY_WINDOW_MS / HISTORY_BUCKET_MS
    var end = Math.floor(nowMs / HISTORY_BUCKET_MS) * HISTORY_BUCKET_MS + HISTORY_BUCKET_MS
    var start = end - HISTORY_WINDOW_MS
    var buckets = []
    for (let i = 0; i < count; i++) {
        buckets.push({start: start + i * HISTORY_BUCKET_MS, ok: 0, total: 0})
    }
    for (const entry of history) {
        var index = Math.floor((Date.parse(entry?.["ts"]) - start) / HISTORY_BUCKET_MS)
        // null means "not measured" (history restored from logs has no MQTT results)
        if (!(index >= 0 && index < count) || entry[key] == null) {
            continue
        }
        buckets[index].total += 1
        if (entry[key]) {
            buckets[index].ok += 1
        }
    }
    return buckets
}

function formatPeriod(startMs, endMs) {
    return `${MSK_DATE_FORMAT.format(new Date(startMs)).replace(", ", " ")}–${MSK_TIME_FORMAT.format(new Date(endMs))}`
}

function formatUptime(buckets) {
    var ok = buckets.reduce((sum, bucket) => sum + bucket.ok, 0)
    var total = buckets.reduce((sum, bucket) => sum + bucket.total, 0)
    if (!total) {
        return "—"
    }
    // floor, so that a single failure never shows up as 100%
    return (Math.floor(ok / total * 1000) / 10).toFixed(1) + "%"
}

function bucketState(bucket) {
    if (!bucket.total) {
        return "nodata"
    }
    if (bucket.ok === bucket.total) {
        return "up"
    }
    return bucket.ok ? "partial" : "down"
}

function showUptime(data) {
    var container = document.getElementById("uptime")
    container.textContent = ""
    if (!data || !Array.isArray(data["history"])) {
        return
    }
    var now = Date.now()
    for (const key of ["services", "mqtt"]) {
        var buckets = buildBuckets(data["history"], key, now)
        var row = document.createElement("div")
        row.setAttribute("class", "uptime-row")
        var name = document.createElement("span")
        name.setAttribute("class", "uptime-name")
        name.textContent = data[key]["name"]
        var bars = document.createElement("div")
        bars.setAttribute("class", "uptime-bars")
        for (const bucket of buckets) {
            var bar = document.createElement("div")
            bar.setAttribute("class", `uptime-bar ${bucketState(bucket)}`)
            var period = formatPeriod(bucket.start, bucket.start + HISTORY_BUCKET_MS)
            bar.setAttribute("title", bucket.total ? `${period}: ${bucket.ok}/${bucket.total} OK` : `${period}: no data`)
            bars.appendChild(bar)
        }
        var percent = document.createElement("span")
        percent.setAttribute("class", "uptime-percent")
        percent.textContent = formatUptime(buckets)
        row.append(name, bars, percent)
        container.appendChild(row)
    }
    var axis = document.createElement("div")
    axis.setAttribute("class", "uptime-axis")
    var from = document.createElement("span")
    from.textContent = "24 h ago"
    var to = document.createElement("span")
    to.textContent = "now"
    axis.append(from, to)
    container.appendChild(axis)
}

function showError(listId, text) {
    var list = document.getElementById(listId)
    list.textContent = ""
    var li = document.createElement("li")
    li.appendChild(document.createTextNode(text))
    li.setAttribute("class", "failure")
    list.appendChild(li)
}

function init() {
    onReady()
    setInterval(onReady, 5 * 60 * 1000)
}

document.addEventListener("DOMContentLoaded", init);
