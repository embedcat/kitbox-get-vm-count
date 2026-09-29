const STATS_MAX_AGE_MS = 26 * 60 * 60 * 1000  // stats are collected once a day at 04:00 and take about 8 minutes
const SERVERS_MAX_AGE_MS = 15 * 60 * 1000
const HISTORY_WINDOW_MS = 24 * 60 * 60 * 1000
const HISTORY_BUCKET_MS = 30 * 60 * 1000
const MSK_DATE_FORMAT = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Moscow", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23"
})
const MSK_TIME_FORMAT = new Intl.DateTimeFormat("en-GB", {timeZone: "Europe/Moscow", hour: "2-digit", minute: "2-digit", hourCycle: "h23"})

const FLEET_TOP_VERSIONS = 6
// firmware names the API gives to machines without a known device: shown last, greyed out, without versions
const UNKNOWN_DEVICES = new Map([["?", "Unknown (?)"], ["Unknown", "Unknown"]])

var uptimeSelected = null  // {key, start} of the bar whose popup is open
var fleetOpen = new Set()  // devices whose versions are shown; kept here because the page re-renders itself
var fleetAllVersions = new Set()  // devices that show every version instead of the top ones
var fleetShownTs = null  // updated_ts of the data the fleet block was built from

function onReady() {
    fetch('./data/data.json', {cache: "no-store"})
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            return response.json()
        })
        .then((data) => {
            document.getElementById("counter").textContent = formatCount(data["counter"])
            showFleet(data)
            showUpdated("updated", data, STATS_MAX_AGE_MS)
        })
        .catch((error) => {
            document.getElementById("counter").textContent = "No data"
            fleetShownTs = null
            document.getElementById("fleet").textContent = ""
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

function formatCount(count) {
    return count.toLocaleString("en-US")
}

function formatShare(count, total, digits) {
    var share = count / total * 100
    var min = 10 ** -digits
    return share < min ? `<${min}%` : share.toFixed(digits) + "%"
}

function pluralVersions(count) {
    return `${count} version${count === 1 ? "" : "s"}`
}

function versionLabel(version) {
    if (version === "?") {
        return "unknown"
    }
    return /^\d/.test(version) ? "v" + version : version  // KV Pos reports "v.2.12", which already has the "v"
}

function makeElement(tag, className, text) {
    var element = document.createElement(tag)
    if (className) {
        element.setAttribute("class", className)
    }
    if (text != null) {
        element.textContent = text
    }
    return element
}

function showFleet(data) {
    var fleet = document.getElementById("fleet")
    var list = document.getElementById("devices")
    if (!Array.isArray(data["devices"])) {
        // data.json written before the version breakdown was added: plain list, as before
        fleetShownTs = null
        fleet.textContent = ""
        list.textContent = ""
        for (const device of data["device_count"]) {
            var li = document.createElement("li")
            li.appendChild(document.createTextNode(device))
            li.setAttribute("class", "device-item")
            list.appendChild(li)
        }
        return
    }
    list.textContent = ""
    // the file changes once a day: do not rebuild (and drop the focus) on every refresh
    if (fleetShownTs === data["updated_ts"]) {
        return
    }
    fleetShownTs = data["updated_ts"]
    fleet.textContent = ""
    const bySize = (a, b) => b["count"] - a["count"]
    var known = data["devices"].filter((device) => !UNKNOWN_DEVICES.has(device["name"])).sort(bySize)
    var unknown = data["devices"].filter((device) => UNKNOWN_DEVICES.has(device["name"])).sort(bySize)
    var widest = Math.max(1, ...(known.length ? known : unknown).map((device) => device["count"]))
    for (const device of known.concat(unknown)) {
        fleet.appendChild(fleetItem(device, data["counter"], widest))
    }
}

function fleetItem(device, total, widest) {
    const name = device["name"]
    const unknown = UNKNOWN_DEVICES.has(name)
    const label = unknown ? UNKNOWN_DEVICES.get(name) : name
    const item = makeElement("div", "fleet-item")
    // an unknown device has no versions to show, so its row is not a button
    const head = makeElement(unknown ? "div" : "button", "fleet-head" + (unknown ? " unknown" : ""))
    head.setAttribute("title", `${label}: ${formatCount(device["count"])} machines · ${formatShare(device["count"], total, 1)} of fleet`)
    var bar = makeElement("span", "fleet-bar")
    var fill = document.createElement("i")
    fill.style.width = `${device["count"] / widest * 100}%`
    bar.appendChild(fill)
    head.append(makeElement("span", unknown ? null : "fleet-chevron"), makeElement("span", "fleet-name", label), bar,
                makeElement("span", "fleet-count", formatCount(device["count"])))
    item.appendChild(head)
    if (unknown) {
        return item
    }

    const panel = makeElement("div", "fleet-panel")
    fillFleetPanel(panel, device)
    const setOpen = (open) => {
        panel.hidden = !open
        item.classList.toggle("open", open)
        head.setAttribute("aria-expanded", String(open))
    }
    head.setAttribute("type", "button")
    setOpen(fleetOpen.has(name))
    head.addEventListener("click", () => {
        if (fleetOpen.has(name)) {
            fleetOpen.delete(name)
        } else {
            fleetOpen.add(name)
        }
        setOpen(fleetOpen.has(name))
    })
    item.appendChild(panel)
    return item
}

function fleetVersionRow(label, count, deviceName, deviceCount, className) {
    var row = makeElement("div", className)
    row.setAttribute("title", `${deviceName} ${label}: ${formatCount(count)} machines · ${formatShare(count, deviceCount, 1)} of ${deviceName}`)
    var track = makeElement("span", "fleet-vtrack")
    var fill = document.createElement("i")
    fill.style.width = `${count / deviceCount * 100}%`
    track.appendChild(fill)
    row.append(makeElement("span", "fleet-vname", label), track, makeElement("span", "fleet-vcount", formatCount(count)),
               makeElement("span", "fleet-vpct", formatShare(count, deviceCount, 0)))
    return row
}

function fillFleetPanel(panel, device) {
    const name = device["name"]
    var versions = device["versions"].slice().sort((a, b) => b["count"] - a["count"])
    var all = fleetAllVersions.has(name)
    var shown = all ? versions : versions.slice(0, FLEET_TOP_VERSIONS)
    panel.textContent = ""
    panel.appendChild(makeElement("p", "fleet-panel-title", `Firmware · ${pluralVersions(versions.length)} · share of ${name}`))
    shown.forEach((version, index) => {
        panel.appendChild(fleetVersionRow(versionLabel(version["version"]), version["count"], name, device["count"], "fleet-vrow" + (index === 0 ? " top" : "")))
    })
    if (!all && versions.length > shown.length) {
        var rest = versions.slice(shown.length)
        var restCount = rest.reduce((sum, version) => sum + version["count"], 0)
        panel.appendChild(fleetVersionRow(`+${rest.length} more`, restCount, name, device["count"], "fleet-vrow rest"))
    }
    if (versions.length > FLEET_TOP_VERSIONS) {
        var toggle = makeElement("button", "fleet-all", all ? "Top versions only" : `All ${versions.length} versions →`)
        toggle.setAttribute("type", "button")
        toggle.addEventListener("click", () => {
            if (fleetAllVersions.has(name)) {
                fleetAllVersions.delete(name)
            } else {
                fleetAllVersions.add(name)
            }
            fillFleetPanel(panel, device)
            panel.querySelector(".fleet-all").focus()
        })
        panel.appendChild(toggle)
    }
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

function bucketText(bucket) {
    var checks = `${bucket.total} check${bucket.total === 1 ? "" : "s"}`
    switch (bucketState(bucket)) {
        case "up":
            return `All ${checks} OK`
        case "down":
            return `All ${checks} failed`
        case "partial":
            return `${bucket.ok} of ${checks} OK`
        default:
            return "No data"
    }
}

function getUptimePopup() {
    var popup = document.getElementById("uptime-popup")
    if (!popup) {
        popup = document.createElement("div")
        popup.setAttribute("id", "uptime-popup")
        popup.setAttribute("class", "uptime-popup")
        popup.setAttribute("role", "status")
        document.body.appendChild(popup)
    }
    return popup
}

function clearUptimeSelection() {
    uptimeSelected = null
    getUptimePopup().classList.remove("visible")
    for (const bar of document.querySelectorAll(".uptime-bar.selected")) {
        bar.classList.remove("selected")
    }
}

function selectUptimeBucket(bars, key, name, buckets, index) {
    var bucket = buckets[index]
    if (uptimeSelected && uptimeSelected.key === key && uptimeSelected.start === bucket.start) {
        return
    }
    clearUptimeSelection()
    uptimeSelected = {key: key, start: bucket.start}
    var bar = bars.children[index]
    bar.classList.add("selected")

    var popup = getUptimePopup()
    popup.textContent = ""
    var title = document.createElement("div")
    title.setAttribute("class", "uptime-popup-title")
    title.textContent = `${name} · ${formatPeriod(bucket.start, bucket.start + HISTORY_BUCKET_MS)}`
    var status = document.createElement("div")
    status.setAttribute("class", `uptime-popup-status ${bucketState(bucket)}`)
    status.textContent = bucketText(bucket)
    popup.append(title, status)

    var margin = 8
    var rect = bar.getBoundingClientRect()
    var left = rect.left + rect.width / 2 - popup.offsetWidth / 2
    left = Math.max(margin, Math.min(left, document.documentElement.clientWidth - popup.offsetWidth - margin))
    var top = rect.top - popup.offsetHeight - margin
    if (top < margin) {
        top = rect.bottom + margin
    }
    popup.style.left = `${left + window.scrollX}px`
    popup.style.top = `${top + window.scrollY}px`
    popup.classList.add("visible")
}

function bucketIndexAt(bars, count, clientX) {
    var rect = bars.getBoundingClientRect()
    return Math.max(0, Math.min(count - 1, Math.floor((clientX - rect.left) / rect.width * count)))
}

function showUptime(data) {
    var container = document.getElementById("uptime")
    container.textContent = ""
    if (!data || !Array.isArray(data["history"])) {
        clearUptimeSelection()
        return
    }
    var now = Date.now()
    var selected = uptimeSelected
    var stillThere = false
    for (const key of ["services", "mqtt"]) {
        // const, not var: the handlers below must keep this row's values, not the last row's
        const buckets = buildBuckets(data["history"], key, now)
        const label = data[key]["name"]
        const bars = document.createElement("div")
        bars.setAttribute("class", "uptime-bars")
        var row = document.createElement("div")
        row.setAttribute("class", "uptime-row")
        var name = document.createElement("span")
        name.setAttribute("class", "uptime-name")
        name.textContent = label
        for (const bucket of buckets) {
            var bar = document.createElement("div")
            bar.setAttribute("class", `uptime-bar ${bucketState(bucket)}`)
            bars.appendChild(bar)
        }
        // a 5 px wide bar is hard to hit with a finger, so pick the bucket by the x position over the whole row
        const select = (event) => selectUptimeBucket(bars, key, label, buckets, bucketIndexAt(bars, buckets.length, event.clientX))
        bars.addEventListener("click", select)
        bars.addEventListener("pointermove", (event) => {
            if (event.pointerType === "mouse") {
                select(event)
            }
        })
        bars.addEventListener("pointerleave", (event) => {
            if (event.pointerType === "mouse") {
                clearUptimeSelection()
            }
        })
        var percent = document.createElement("span")
        percent.setAttribute("class", "uptime-percent")
        percent.textContent = formatUptime(buckets)
        row.append(name, bars, percent)
        container.appendChild(row)

        // the page refreshes itself: keep the popup on the same bar if it is still within the window
        var index = selected && selected.key === key ? buckets.findIndex((bucket) => bucket.start === selected.start) : -1
        if (index >= 0) {
            uptimeSelected = null
            selectUptimeBucket(bars, key, label, buckets, index)
            stillThere = true
        }
    }
    if (selected && !stillThere) {
        clearUptimeSelection()
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
    document.addEventListener("pointerdown", (event) => {
        if (!event.target.closest(".uptime-bars")) {
            clearUptimeSelection()
        }
    })
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            clearUptimeSelection()
        }
    })
    window.addEventListener("resize", clearUptimeSelection)
}

document.addEventListener("DOMContentLoaded", init);
