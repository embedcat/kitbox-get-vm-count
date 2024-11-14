function onReady() {
    fetch('./data.json')
        .then((response) => response.json())
        .then((data) => {
            document.getElementById("counter").innerHTML = String(data["counter"])
            var list = document.getElementById("devices")
            for (const device of data["device_count"]) {
                var li = document.createElement("li")
                li.appendChild(document.createTextNode(device))
                li.setAttribute("class", "device-item")
                list.appendChild(li)
            }
            document.getElementById("updated").innerHTML = String(data["updated_datetime"])
        });
    fetch('./server_status.json')
        .then((response) => response.json())
        .then((data) => {
            var list = document.getElementById("servers")
            var li_services = document.createElement("li")
            li_services.appendChild(document.createTextNode(`Services: ${data["services"] ? "OK" : "FAILURE"}`))
            li_services.setAttribute("class", data["services"] ? "servers-item" : "failure")
            list.appendChild(li_services)
            var li_mqtt = document.createElement("li")
            li_mqtt.appendChild(document.createTextNode(`MQTT: ${data["mqtt"] ? "OK" : "FAILURE"}`))
            li_mqtt.setAttribute("class", data["mqtt"] ? "servers-item" : "failure")
            list.appendChild(li_mqtt)
            document.getElementById("updated-servers").innerHTML = String(data["updated_datetime"])
            if (data["last_failure"]) {
                document.getElementById("last-failure").innerHTML = String("Last failure:" + data["last_failure"])
            }
        });
}
document.addEventListener("DOMContentLoaded", onReady);
