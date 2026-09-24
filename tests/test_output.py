from datetime import datetime
import json
import os

import check_servers
import get_active_modems
import output
from KVApi import MSK


def test_output_dir_default_is_data_next_to_scripts(monkeypatch):
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    path = output.output_dir()
    assert path == os.path.join(os.path.dirname(os.path.abspath(output.__file__)), "data")
    assert os.path.isdir(path)


def test_output_dir_from_env_is_created(monkeypatch, tmp_path):
    target = tmp_path / "out" / "nested"
    monkeypatch.setenv("OUTPUT_DIR", str(target))
    assert output.output_dir() == str(target)
    assert target.is_dir()


def test_timestamps_iso_with_msk_offset():
    ts = output.timestamps(datetime(2026, 9, 24, 11, 26, 35, tzinfo=MSK))
    assert ts == {"updated_datetime": "24/09/2026 11:26:35", "updated_ts": "2026-09-24T11:26:35+03:00"}


def test_write_atomic_replaces_and_leaves_no_temp(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("old")
    output.write_atomic(str(path), "new")
    assert path.read_text() == "new"
    assert os.listdir(tmp_path) == ["data.json"]


def test_data_json_has_parsable_timestamp(tmp_path):
    path = tmp_path / "data.json"
    get_active_modems.create_json(counter=1, device_count=["KPL - 1"], filepath=str(path))
    data = json.loads(path.read_text())
    assert datetime.fromisoformat(data["updated_ts"]).utcoffset() == MSK.utcoffset(None)
    assert data["updated_datetime"]


def test_server_status_has_parsable_timestamp(tmp_path):
    path = tmp_path / "server_status.json"
    check_servers.create_json(services={"name": "Services", "ok": True, "detail": "1/1 OK"}, mqtt={"name": "MQTT", "ok": True, "detail": "OK"},
                              filepath=str(path))
    data = json.loads(path.read_text())
    assert datetime.fromisoformat(data["updated_ts"]).utcoffset() == MSK.utcoffset(None)
