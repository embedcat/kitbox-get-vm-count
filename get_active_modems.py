import json
import logging
import os
import sys
import output
import parse_fw_versions
from kitvending_api import MSK, KitVendingClient, KitVendingError
from datetime import datetime
from dotenv import load_dotenv


TEMP_FILENAME = "vend_machines.txt"
VERSION_FILENAME = "version_info.txt"
DATA_JSON_FILENAME = "data.json"


def create_json(counter: int, device_count: list[str], filepath: str) -> None:
    data = {
        "counter": counter,
        "device_count": device_count,
        **output.timestamps(),
    }
    output.write_atomic(filepath, json.dumps(data))


if __name__ == "__main__":
    load_dotenv(override=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    api = KitVendingClient.from_env()

    script_path = os.path.dirname(os.path.abspath(__file__))
    file = f"{script_path}/{TEMP_FILENAME}"
    if os.path.exists(file):
        os.remove(file)

    version_file = os.path.join(output.output_dir(), VERSION_FILENAME)
    json_file = os.path.join(output.output_dir(), DATA_JSON_FILENAME)

    try:
        vms = api.get_vm_states()
    except KitVendingError as e:
        print(f"Error. {e}")
        sys.exit(1)
    with open(file, "w") as f:
        json.dump({"VendingMachines": vms}, f, indent=4)

    active_vms, invalid_count = parse_fw_versions.filter_active(vms, datetime.now(MSK))
    if invalid_count:
        print(f"VMs without valid DateTime: {invalid_count}")
    actual_count = len(active_vms)
    device_count = parse_fw_versions.parse_file(vms=active_vms, full_version_info_file=version_file)
    create_json(counter=actual_count, device_count=device_count, filepath=json_file)
