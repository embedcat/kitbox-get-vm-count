from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from collections import Counter
import operator


@dataclass
class Firmware:
    device: str
    version: str
    count: int


def parse_file(file: str, full_version_info_file: str = None) -> list[str]:
    data = {}
    with open(file) as f:
        data = json.load(f)
    vms = data["VendingMachines"]
    now = datetime.now()
    fws = [vm["Firmware"] for vm in vms if now - datetime.strptime(vm["DateTime"], "%d.%m.%Y %H:%M:%S") <= timedelta(weeks=2)]
    counter = dict(Counter(fws))
    items = []
    for k, v in counter.items():
        tmp = k.split(" ")
        device = "".join(tmp[:-1])
        version = tmp[-1]
        item = Firmware(device=device, version=version, count=v)
        items.append(item)

    items = sorted(items, key=operator.attrgetter("device", "version"))
    devices = list(set([elem.device for elem in items]))
    output = []
    version_info = []
    for i, device in enumerate(devices):
        current_device = [elem for elem in items if elem.device == device]
        current_device_count = sum(elem.count for elem in current_device)
        output.append(f"{device} - {current_device_count}")
        if full_version_info_file:
            version_info.append(f"{device} - {current_device_count}\n")
            for version, count in [(elem.version, elem.count) for elem in current_device]:
                version_info.append(f"v{version} - {count}\n")
            version_info.append("=======\n")
    if full_version_info_file:
        with open(full_version_info_file, "w") as f:
            f.writelines(version_info)
    output.sort()
    return output


if __name__ == "__main__":
    output = parse_file("vend_machines.txt", "version_info.txt")
