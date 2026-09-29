from datetime import datetime, timedelta

import parse_fw_versions


def _vm(firmware, dt):
    return {"Firmware": firmware, "DateTime": dt.strftime("%d.%m.%Y %H:%M:%S")}


def test_filter_active_excludes_old():
    now = datetime(2026, 1, 15, 12, 0, 0)
    vms = [
        _vm("KPL 1.09", now - timedelta(days=1)),
        _vm("KPM 2.34", now - timedelta(weeks=3)),
    ]
    active, invalid = parse_fw_versions.filter_active(vms, now)
    assert len(active) == 1
    assert active[0]["Firmware"] == "KPL 1.09"
    assert invalid == 0


def test_parse_file_groups_by_device_and_version():
    vms = [
        {"Firmware": "KPL 1.09"},
        {"Firmware": "KPL 1.09"},
        {"Firmware": "Kit Box Lite 16.130"},
    ]
    output = parse_fw_versions.parse_file(vms)
    assert output == ["KPL - 2", "KitBoxLite - 1"]


def test_build_devices_groups_versions_of_each_device():
    vms = [
        {"Firmware": "Kit Box Lite 16.130"},
        {"Firmware": "Kit Box Lite 16.130"},
        {"Firmware": "Kit Box Lite 16.103"},
        {"Firmware": "KPL 1.09"},
    ]
    assert parse_fw_versions.build_devices(vms) == [
        {"name": "KPL", "count": 1, "versions": [{"version": "1.09", "count": 1}]},
        {"name": "KitBoxLite", "count": 3, "versions": [{"version": "16.103", "count": 1}, {"version": "16.130", "count": 2}]},
    ]


def test_build_devices_counts_add_up_to_the_number_of_machines():
    vms = [{"Firmware": "KPL 1.09"}, {"Firmware": "KPL 1.08"}, {"Firmware": "?"}, {"Firmware": None}]
    devices = parse_fw_versions.build_devices(vms)
    assert sum(device["count"] for device in devices) == len(vms)
    for device in devices:
        assert device["count"] == sum(version["count"] for version in device["versions"])


def test_build_devices_keeps_unknown_firmware_as_a_device():
    devices = parse_fw_versions.build_devices([{"Firmware": "?"}])
    assert devices == [{"name": "?", "count": 1, "versions": [{"version": parse_fw_versions.UNKNOWN_VERSION, "count": 1}]}]


def test_device_lines_match_the_page_list():
    devices = parse_fw_versions.build_devices([{"Firmware": "KPL 1.09"}, {"Firmware": "KPL 1.09"}])
    assert parse_fw_versions.device_lines(devices) == ["KPL - 2"]


def test_parse_file_writes_version_info(tmp_path):
    vms = [{"Firmware": "KPL 1.09"}, {"Firmware": "KPL 1.09"}]
    out_file = tmp_path / "version_info.txt"
    parse_fw_versions.parse_file(vms, full_version_info_file=str(out_file))
    content = out_file.read_text()
    assert "KPL - 2" in content
    assert "v1.09 - 2" in content


def test_parse_file_no_file_when_not_requested(tmp_path):
    vms = [{"Firmware": "KPL 1.09"}]
    out_file = tmp_path / "should_not_exist.txt"
    parse_fw_versions.parse_file(vms)
    assert not out_file.exists()
