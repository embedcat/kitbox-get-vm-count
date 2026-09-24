from datetime import timedelta
import json
import time

import requests

import check_servers


class FakeResponse:
    def __init__(self, status_code, elapsed_ms):
        self.status_code = status_code
        self.elapsed = timedelta(milliseconds=elapsed_ms)


def test_check_services_api_checks_all_urls_no_early_exit(monkeypatch):
    calls = []

    def fake_post(url, timeout):
        calls.append(url)
        if url == "http://a.example/":
            raise requests.exceptions.ConnectTimeout("timed out")
        if url == "http://b.example/":
            return FakeResponse(500, 10)
        return FakeResponse(200, 15)

    monkeypatch.setattr(check_servers.requests, "post", fake_post)
    urls = ["http://a.example/", "http://b.example/", "http://c.example/"]
    results = check_servers.check_services_api(urls)

    assert calls == urls
    assert results[0] == {"name": "a.example", "ok": False, "detail": "timed out"}
    assert results[1]["name"] == "b.example"
    assert results[1]["ok"] is False
    assert results[1]["detail"].startswith("500")
    assert results[2]["name"] == "c.example"
    assert results[2]["ok"] is True
    assert results[2]["detail"].startswith("200")


class FakeMqttClient:
    def __init__(self, mode):
        self.mode = mode
        self.on_connect = None
        self.on_connect_fail = None
        self.connect_timeout = None

    def username_pw_set(self, username, password):
        pass

    def connect(self, broker, port):
        if self.mode == "connect_error":
            raise OSError("connection refused")

    def loop_start(self):
        if self.mode == "success":
            self.on_connect(self, None, None, 0, None)
        elif self.mode == "refused":
            self.on_connect(self, None, None, 135, None)
        elif self.mode == "connect_fail":
            self.on_connect_fail(self, None)

    def loop_stop(self):
        pass

    def disconnect(self):
        pass


def _fake_client_factory(mode):
    def factory(callback_api_version, client_id=None):
        return FakeMqttClient(mode)
    return factory


def test_check_mqtt_success(monkeypatch):
    monkeypatch.setattr(check_servers.mqtt_client, "Client", _fake_client_factory("success"))
    result = check_servers.check_mqtt("broker", 1883, "cid", "user", "pass", timeout=1)
    assert result == {"name": "MQTT", "ok": True, "detail": "OK"}


def test_check_mqtt_broker_refuses(monkeypatch):
    monkeypatch.setattr(check_servers.mqtt_client, "Client", _fake_client_factory("refused"))
    result = check_servers.check_mqtt("broker", 1883, "cid", "user", "pass", timeout=1)
    assert result["name"] == "MQTT"
    assert result["ok"] is False
    assert result["detail"] == "135"


def test_check_mqtt_connect_fail_callback(monkeypatch):
    monkeypatch.setattr(check_servers.mqtt_client, "Client", _fake_client_factory("connect_fail"))
    result = check_servers.check_mqtt("broker", 1883, "cid", "user", "pass", timeout=1)
    assert result["ok"] is False


def test_check_mqtt_timeout_no_callback(monkeypatch):
    monkeypatch.setattr(check_servers.mqtt_client, "Client", _fake_client_factory("timeout"))
    start = time.monotonic()
    result = check_servers.check_mqtt("broker", 1883, "cid", "user", "pass", timeout=0.2)
    elapsed = time.monotonic() - start
    assert result["ok"] is False
    assert elapsed < 5


def test_check_mqtt_connect_raises(monkeypatch):
    monkeypatch.setattr(check_servers.mqtt_client, "Client", _fake_client_factory("connect_error"))
    result = check_servers.check_mqtt("broker", 1883, "cid", "user", "pass", timeout=1)
    assert result["name"] == "MQTT"
    assert result["ok"] is False
    assert "connection refused" in result["detail"]


def test_summarize_services_all_ok():
    results = [{"name": "a.example", "ok": True, "detail": "200, 10 ms"}, {"name": "b.example", "ok": True, "detail": "200, 12 ms"}]
    assert check_servers.summarize_services(results) == {"name": "Services", "ok": True, "detail": "2/2 OK"}


def test_summarize_services_one_down_is_failure():
    results = [
        {"name": "a.example", "ok": True, "detail": "200, 10 ms"},
        {"name": "b.example", "ok": False, "detail": "HTTPConnectionPool(host='b.example', port=80): timed out"},
        {"name": "c.example", "ok": True, "detail": "200, 12 ms"},
    ]
    assert check_servers.summarize_services(results) == {"name": "Services", "ok": False, "detail": "2/3 OK"}


def test_create_json_contains_no_service_addresses(tmp_path):
    filepath = str(tmp_path / "server_status.json")
    results = [
        {"name": "a.example", "ok": True, "detail": "200, 10 ms"},
        {"name": "b.example", "ok": False, "detail": "HTTPConnectionPool(host='b.example', port=80): timed out"},
    ]
    check_servers.create_json(services=check_servers.summarize_services(results), mqtt={"name": "MQTT", "ok": True, "detail": "OK"},
                              filepath=filepath)

    with open(filepath) as f:
        content = f.read()
    assert "example" not in content


def test_create_json_merges_last_failure(tmp_path):
    filepath = str(tmp_path / "server_status.json")
    services_first = {"name": "Services", "ok": False, "detail": "1/2 OK"}
    mqtt_first = {"name": "MQTT", "ok": False, "detail": "135"}
    check_servers.create_json(services=services_first, mqtt=mqtt_first, filepath=filepath)

    with open(filepath) as f:
        data = json.load(f)
    assert data["services"]["ok"] is False
    first_failure_time = data["services"]["last_failure"]
    assert data["mqtt"]["last_failure"]

    services_second = {"name": "Services", "ok": True, "detail": "2/2 OK"}
    mqtt_second = {"name": "MQTT", "ok": True, "detail": "OK"}
    check_servers.create_json(services=services_second, mqtt=mqtt_second, filepath=filepath)

    with open(filepath) as f:
        data = json.load(f)
    assert data["services"]["ok"] is True
    assert data["services"]["last_failure"] == first_failure_time
    assert data["mqtt"]["ok"] is True
    assert data["mqtt"]["last_failure"]


def test_create_json_handles_old_formats_without_crashing(tmp_path):
    filepath = str(tmp_path / "server_status.json")
    old_formats = [
        {"services": True, "mqtt": False, "updated_datetime": "01/01/2024 00:00:00", "last_failure": "01/01/2024 00:00:00"},
        {"services": [{"name": "a.example", "ok": False, "detail": "500", "last_failure": "01/01/2024 00:00:00"}],
         "mqtt": {"name": "MQTT", "ok": True, "detail": "OK"}, "updated_datetime": "01/01/2024 00:00:00"},
    ]
    services = {"name": "Services", "ok": True, "detail": "1/1 OK"}
    mqtt = {"name": "MQTT", "ok": True, "detail": "OK"}
    for old in old_formats:
        with open(filepath, "w") as f:
            json.dump(old, f)

        check_servers.create_json(services=services, mqtt=mqtt, filepath=filepath)

        with open(filepath) as f:
            data = json.load(f)
        assert data["services"] == services
        assert data["mqtt"] == mqtt
