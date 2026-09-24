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
