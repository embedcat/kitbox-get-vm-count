function onReady() {
    fetch('./data.json', {cache: "no-store"})
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
            document.getElementById("updated").textContent = String(data["updated_datetime"])
        })
        .catch((error) => {
            document.getElementById("counter").textContent = "No data"
            showError("devices", `data.json unavailable: ${error.message}`)
            document.getElementById("updated").textContent = ""
        });
    fetch('./server_status.json', {cache: "no-store"})
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
            document.getElementById("updated-servers").textContent = String(data["updated_datetime"])
            document.getElementById("last-failure").textContent = lastFailures.length ? "Last failure — " + lastFailures.join(", ") : ""
        })
        .catch((error) => {
            showError("servers", `server_status.json unavailable: ${error.message}`)
            document.getElementById("updated-servers").textContent = ""
            document.getElementById("last-failure").textContent = ""
        });
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
