from datetime import datetime
import json
import os
import threading
from urllib.parse import urlsplit
import requests
from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv


DATA_JSON_FILENAME = "server_status.json"

SERVICES_API_TIMEOUT = (5, 15)
MQTT_DEFAULT_TIMEOUT = 10


def check_services_api(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        name = urlsplit(url).netloc
        try:
            r = requests.post(url=url, timeout=SERVICES_API_TIMEOUT)
        except requests.exceptions.RequestException as e:
            results.append({"name": name, "ok": False, "detail": str(e)})
            continue
        ms = r.elapsed.total_seconds() * 1000
        detail = f"{r.status_code}, {ms:.0f} ms"
        results.append({"name": name, "ok": r.status_code == 200, "detail": detail})
    return results


def summarize_services(results: list[dict]) -> dict:
    ok_count = sum(1 for r in results if r["ok"])
    return {"name": "Services", "ok": bool(results) and ok_count == len(results), "detail": f"{ok_count}/{len(results)} OK"}


def check_mqtt(broker: str, port: int, client_id: str, username: str, password: str, timeout: float = MQTT_DEFAULT_TIMEOUT) -> dict:
    connected = threading.Event()
    result = {"ok": False, "detail": "Timed out waiting for CONNACK"}

    def on_connect(client, userdata, flags, reason_code, properties):
        result["ok"] = reason_code == 0
        result["detail"] = "OK" if reason_code == 0 else str(reason_code)
        connected.set()

    def on_connect_fail(client, userdata):
        result["detail"] = "Connection failed"
        connected.set()

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_connect_fail = on_connect_fail
    client.connect_timeout = timeout

    try:
        client.connect(broker, port)
    except Exception as e:
        return {"name": "MQTT", "ok": False, "detail": str(e)}

    client.loop_start()
    connected.wait(timeout)
    client.loop_stop()
    client.disconnect()

    return {"name": "MQTT", "ok": result["ok"], "detail": result["detail"]}


def _load_previous(filepath: str) -> dict:
    try:
        with open(filepath, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, ValueError):
        return {}
    if not isinstance(data.get("services"), dict) or not isinstance(data.get("mqtt"), dict):
        return {}
    return data


def _with_last_failure(entry: dict, previous_entry: dict = None) -> dict:
    last_failure = previous_entry.get("last_failure") if previous_entry else None
    if not entry["ok"]:
        last_failure = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    result = dict(entry)
    if last_failure:
        result["last_failure"] = last_failure
    return result


def create_json(services: dict, mqtt: dict, filepath: str) -> None:
    previous = _load_previous(filepath)

    data = {
        "services": _with_last_failure(services, previous.get("services")),
        "mqtt": _with_last_failure(mqtt, previous.get("mqtt")),
        "updated_datetime": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
    }

    with open(filepath, "w") as out:
        json.dump(data, out)


if __name__ == '__main__':
    load_dotenv(override=True)

    script_path = os.path.dirname(os.path.abspath(__file__))
    json_file = f"{script_path}/{DATA_JSON_FILENAME}"

    services_results = check_services_api(urls=os.getenv("SERVICES_API_URLS").split(","))
    for r in services_results:
        print(f"{r['name']}: {'OK' if r['ok'] else 'FAILURE'} ({r['detail']})")
    services_status = summarize_services(services_results)
    mqtt_timeout = float(os.getenv("MQTT_TIMEOUT", MQTT_DEFAULT_TIMEOUT))
    mqtt_status = check_mqtt(broker=os.getenv("MQTT_BROKER"),
                              port=int(os.getenv("MQTT_PORT")),
                              client_id=os.getenv("MQTT_CLIENT_ID"),
                              username=os.getenv("MQTT_USERNAME"),
                              password=os.getenv("MQTT_PASSWORD"),
                              timeout=mqtt_timeout)

    create_json(services=services_status, mqtt=mqtt_status, filepath=json_file)
