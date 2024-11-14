from datetime import datetime
import json
import os
import requests
from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv


DATA_JSON_FILENAME = "server_status.json"


def check_services_api(urls: list[str]) -> bool:
    for url in urls:
        try:
            r = requests.post(url=url)
        except requests.exceptions.RequestException as e:
            return False
        if r.status_code != 200:
            return False
    return True


is_mqtt_connected = False


def check_mqtt(broker: str, port: int, client_id: str, username: str, password: str) -> bool:
    def on_connect(client, userdata, flags, reason_code, properties):
        global is_mqtt_connected
        is_mqtt_connected = reason_code == 0

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    try:
        client.connect(broker, port)
        client.loop_start()
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        pass

    return is_mqtt_connected


def create_json(services: bool, mqtt: bool, filepath: str) -> None:
    data = {}
    try:
        with open(filepath, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        pass

    data["services"] = services
    data["mqtt"] = mqtt
    data["updated_datetime"] = str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    if not services or not mqtt:
        data["last_failure"] = str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    with open(filepath, "w") as out:
        json.dump(data, out)


if __name__ == '__main__':
    load_dotenv(override=True)

    script_path = os.path.dirname(os.path.abspath(__file__))
    json_file = f"{script_path}/{DATA_JSON_FILENAME}"

    services_ok = check_services_api(urls=os.getenv("SERVICES_API_URLS").split(","))
    mqtt_ok = check_mqtt(broker=os.getenv("MQTT_BROKER"),
                         port=int(os.getenv("MQTT_PORT")),
                         client_id=os.getenv("MQTT_CLIENT_ID"),
                         username=os.getenv("MQTT_USERNAME"),
                         password=os.getenv("MQTT_PASSWORD"))

    create_json(services=services_ok, mqtt=mqtt_ok, filepath=json_file)
