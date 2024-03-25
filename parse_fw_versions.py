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


def parse_file(file: str, full_version_info: bool = False) -> list[str]:
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
    for i, device in enumerate(devices):
        current_device = [elem for elem in items if elem.device == device]
        current_device_count = sum(elem.count for elem in current_device)
        # print(current_device)
        print(f"{i} - {device}. Count = {current_device_count}")
        output.append(f"{device} - {current_device_count}")
        if full_version_info:
            for version, count in [(elem.version, elem.count) for elem in current_device]:
                print(f"v{version} - {count}")
            print("=======")
    output.sort()
    return output


if __name__ == "__main__":
    output = parse_file("company7_15_03_2024_16_33_17_vm_states.txt")
    # parse_file("company380637_15_03_2024_16_27_21_vm_states.txt")
