from datetime import datetime, timedelta

from KVApi import MSK
import parse_fw_versions


def test_parse_datetime_valid():
    dt = parse_fw_versions.parse_datetime("15.01.2026 12:00:00")
    assert dt == datetime(2026, 1, 15, 12, 0, 0, tzinfo=MSK)


def test_parse_datetime_empty_string():
    assert parse_fw_versions.parse_datetime("") is None


def test_parse_datetime_none():
    assert parse_fw_versions.parse_datetime(None) is None


def test_parse_datetime_garbage():
    assert parse_fw_versions.parse_datetime("garbage") is None


def test_filter_active_handles_broken_dates_without_crashing():
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=MSK)
    vms = [
        {"Firmware": "KPL 1.09", "DateTime": ""},
        {"Firmware": "KPL 1.09", "DateTime": None},
        {"Firmware": "KPL 1.09", "DateTime": "garbage"},
        {"Firmware": "KPL 1.09"},
        {"Firmware": "KPL 1.09", "DateTime": (now - timedelta(days=1)).strftime("%d.%m.%Y %H:%M:%S")},
        {"Firmware": "KPM 2.34", "DateTime": (now - timedelta(weeks=3)).strftime("%d.%m.%Y %H:%M:%S")},
    ]
    active, invalid = parse_fw_versions.filter_active(vms, now)
    assert invalid == 4
    assert len(active) == 1
    assert active[0]["Firmware"] == "KPL 1.09"


def test_filter_active_naive_now_does_not_crash():
    now = datetime(2026, 1, 15, 12, 0, 0)
    vms = [{"Firmware": "KPL 1.09", "DateTime": (now - timedelta(days=1)).strftime("%d.%m.%Y %H:%M:%S")}]
    active, invalid = parse_fw_versions.filter_active(vms, now)
    assert invalid == 0
    assert len(active) == 1
