from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from collections import Counter

from kitvending_api import MSK, parse_datetime
from output import write_atomic

UNKNOWN_VERSION = "?"


@dataclass
class Firmware:
    device: str
    version: str
    count: int


def filter_active(vms: list, now: datetime) -> tuple[list, int]:
    if now.tzinfo is None:
        now = now.replace(tzinfo=MSK)
    active = []
    invalid = 0
    for vm in vms:
        dt = parse_datetime(vm.get("DateTime"))
        if dt is None:
            invalid += 1
            continue
        if now - dt <= timedelta(weeks=2):
            active.append(vm)
    return active, invalid


def normalize_version(version: str) -> str:
    major, dot, rest = version.partition(".")
    return (str(int(major)) if major.isdigit() else major) + dot + rest


def parse_firmware(firmware) -> tuple[str, str]:
    if not firmware:
        return "Unknown", UNKNOWN_VERSION
    parts = firmware.split(" ")
    if len(parts) == 1:
        return parts[0], UNKNOWN_VERSION
    device = "".join(parts[:-1])
    version = normalize_version(parts[-1])
    return device, version


def version_sort_key(version: str):
    parts = version.split(".")
    if all(part.isdigit() for part in parts):
        return (0, tuple(int(part) for part in parts))
    return (1, version)


def build_devices(vms: list) -> list[dict]:
    fws = [vm.get("Firmware") for vm in vms]
    counter = dict(Counter(fws))
    grouped = {}
    for firmware, count in counter.items():
        key = parse_firmware(firmware)
        grouped[key] = grouped.get(key, 0) + count

    items = [Firmware(device=device, version=version, count=count) for (device, version), count in grouped.items()]
    items = sorted(items, key=lambda item: (item.device, version_sort_key(item.version)))

    devices = []
    for device in sorted(set(item.device for item in items)):
        versions = [{"version": item.version, "count": item.count} for item in items if item.device == device]
        devices.append({"name": device, "count": sum(version["count"] for version in versions), "versions": versions})
    return devices


def device_lines(devices: list[dict]) -> list[str]:
    return [f"{device['name']} - {device['count']}" for device in devices]


def write_version_info(devices: list[dict], path: str) -> None:
    version_info = []
    for device in devices:
        version_info.append(f"{device['name']} - {device['count']}\n")
        for version in device["versions"]:
            version_info.append(f"v{version['version']} - {version['count']}\n")
        version_info.append("=======\n")
    write_atomic(path, "".join(version_info))


def parse_file(vms: list, full_version_info_file: str = None) -> list[str]:
    devices = build_devices(vms)
    if full_version_info_file:
        write_version_info(devices, full_version_info_file)
    return device_lines(devices)


if __name__ == "__main__":
    with open("vend_machines.txt") as f:
        data = json.load(f)
    active_vms, invalid_count = filter_active(data["VendingMachines"], datetime.now(MSK))
    if invalid_count:
        print(f"VMs without valid DateTime: {invalid_count}")
    output = parse_file(active_vms, "version_info.txt")
