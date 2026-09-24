import parse_fw_versions


def test_normalize_version_strips_leading_zeros():
    assert parse_fw_versions.normalize_version("016.131") == "16.131"
    assert parse_fw_versions.normalize_version("16.131") == "16.131"
    assert parse_fw_versions.normalize_version("4.47") == "4.47"


def test_normalize_version_keeps_minor_as_is():
    assert parse_fw_versions.normalize_version("1.09") == "1.09"
    assert parse_fw_versions.normalize_version("016.09") == "16.09"


def test_normalize_version_leaves_non_numeric_parts_alone():
    assert parse_fw_versions.normalize_version("16.13a") == "16.13a"


def test_version_sort_key_numeric_order():
    versions = ["4.100", "4.47", "4.9"]
    ordered = sorted(versions, key=parse_fw_versions.version_sort_key)
    assert ordered == ["4.9", "4.47", "4.100"]


def test_version_sort_key_non_numeric_goes_last():
    versions = ["2.0", "beta", "1.0", "alpha"]
    ordered = sorted(versions, key=parse_fw_versions.version_sort_key)
    assert ordered == ["1.0", "2.0", "alpha", "beta"]


def test_leading_zero_versions_merge_counts(tmp_path):
    vms = [
        {"Firmware": "Kit Pos Master 016.131"},
        {"Firmware": "Kit Pos Master 016.131"},
        {"Firmware": "Kit Pos Master 16.131"},
    ]
    out_file = tmp_path / "version_info.txt"
    output = parse_fw_versions.parse_file(vms, full_version_info_file=str(out_file))
    assert output == ["KitPosMaster - 3"]
    content = out_file.read_text()
    assert content.count("v16.131 - 3") == 1
    assert "016.131" not in content


def test_empty_or_none_firmware_is_unknown_device():
    vms = [{"Firmware": ""}, {"Firmware": None}, {}]
    output = parse_fw_versions.parse_file(vms)
    assert output == ["Unknown - 3"]


def test_single_word_firmware_has_unknown_version(tmp_path):
    vms = [{"Firmware": "KitPosLite"}]
    out_file = tmp_path / "version_info.txt"
    parse_fw_versions.parse_file(vms, full_version_info_file=str(out_file))
    content = out_file.read_text()
    assert "KitPosLite - 1" in content
    assert f"v{parse_fw_versions.UNKNOWN_VERSION} - 1" in content


def test_device_order_matches_output_alphabetical_order(tmp_path):
    vms = [
        {"Firmware": "KPM 2.34"},
        {"Firmware": "KPL 1.09"},
        {"Firmware": "Kit Box Lite 16.130"},
    ]
    out_file = tmp_path / "version_info.txt"
    output = parse_fw_versions.parse_file(vms, full_version_info_file=str(out_file))
    assert output == sorted(output)
    blocks = [b.strip().split("\n")[0].split(" - ")[0] for b in out_file.read_text().split("=======") if b.strip()]
    assert blocks == [line.split(" - ")[0] for line in output]


def test_repeated_runs_produce_identical_output(tmp_path):
    vms = [
        {"Firmware": "KPM 2.34"},
        {"Firmware": "KPL 1.09"},
        {"Firmware": "Kit Box Lite 16.130"},
        {"Firmware": "Kit Box Lite 16.103"},
        {"Firmware": "Kit Pos Master 016.131"},
        {"Firmware": "Kit Pos Master 16.131"},
    ]
    out_file_1 = tmp_path / "v1.txt"
    out_file_2 = tmp_path / "v2.txt"
    output_1 = parse_fw_versions.parse_file(vms, full_version_info_file=str(out_file_1))
    output_2 = parse_fw_versions.parse_file(vms, full_version_info_file=str(out_file_2))
    assert output_1 == output_2
    assert out_file_1.read_text() == out_file_2.read_text()
