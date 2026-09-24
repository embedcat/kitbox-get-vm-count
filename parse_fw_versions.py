from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from collections import Counter

from KVApi import MSK

UNKNOWN_VERSION = "?"


@dataclass
class Firmware:
    device: str
    version: str
    count: int


def parse_datetime(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d.%m.%Y %H:%M:%S").replace(tzinfo=MSK)
    except (ValueError, TypeError):
        return None


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


def parse_file(vms: list, full_version_info_file: str = None) -> list[str]:
    fws = [vm.get("Firmware") for vm in vms]
    counter = dict(Counter(fws))
    grouped = {}
    for firmware, count in counter.items():
        key = parse_firmware(firmware)
        grouped[key] = grouped.get(key, 0) + count

    items = [Firmware(device=device, version=version, count=count) for (device, version), count in grouped.items()]
    items = sorted(items, key=lambda item: (item.device, version_sort_key(item.version)))

    devices = sorted(set(item.device for item in items))
    output = []
    version_info = []
    for device in devices:
        current_device = [item for item in items if item.device == device]
        current_device_count = sum(item.count for item in current_device)
        output.append(f"{device} - {current_device_count}")
        if full_version_info_file:
            version_info.append(f"{device} - {current_device_count}\n")
            for item in current_device:
                version_info.append(f"v{item.version} - {item.count}\n")
            version_info.append("=======\n")
    if full_version_info_file:
        with open(full_version_info_file, "w") as f:
            f.writelines(version_info)
    return output


if __name__ == "__main__":
    with open("vend_machines.txt") as f:
        data = json.load(f)
    active_vms, invalid_count = filter_active(data["VendingMachines"], datetime.now(MSK))
    if invalid_count:
        print(f"VMs without valid DateTime: {invalid_count}")
    output = parse_file(active_vms, "version_info.txt")
