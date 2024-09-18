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
}
document.addEventListener("DOMContentLoaded", onReady);
