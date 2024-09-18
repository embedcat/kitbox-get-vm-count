import json
import os
import sys
import parse_fw_versions
from KVApi import KVApi, APIClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup


TEMP_FILENAME = "vend_machines.txt"
VERSION_FILENAME = "version_info.txt"
DATA_JSON_FILENAME = "data.json"


def count_vms(vms: list) -> int:
    now = datetime.now()
    return len([elem for elem in vms if now - datetime.strptime(elem["DateTime"], "%d.%m.%Y %H:%M:%S") <= timedelta(weeks=2)])


def update_html(counter: int, device_count: list[str], filepath: str) -> None:
    if not filepath:
        return
    with open(filepath) as file:
        html = file.read()
        soup = BeautifulSoup(html, "html.parser")
    tag_counter = soup.find(id="counter")
    tag_counter.string = str(counter)
    tag_updated = soup.find(id="updated")
    tag_updated.string = str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    tag_devices = soup.find(id="devices")
    tag_devices.clear()
    for item in device_count:
        li = soup.new_tag("li", attrs={"class": "device-item"})
        li.string = item
        tag_devices.append(li)
    with open(filepath, "w") as file:
        file.write(str(soup))


def create_json(counter: int, device_count: list[str], filepath: str) -> None:
    data = {
        "counter": counter,
        "device_count": device_count,
        "updated_datetime": str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
    }
    with open(filepath, "w") as out:
        json.dump(data, out)


if __name__ == "__main__":
    load_dotenv(override=True)
    client = APIClient(company_id=os.getenv("COMPANY_ID"), user_login=os.getenv("USER_LOGIN"), user_password=os.getenv("USER_PASSWORD"))
    api = KVApi(client=client)

    script_path = os.path.dirname(os.path.abspath(__file__))
    file = f"{script_path}/{TEMP_FILENAME}"
    if os.path.exists(file):
        os.remove(file)

    version_file = f"{script_path}/{VERSION_FILENAME}"
    json_file = f"{script_path}/{DATA_JSON_FILENAME}"

    response = api.get_vm_states(file_path_to_dump=file)
    if response:
        if response["ResultCode"] == 0:
            actual_count = count_vms(vms=response["VendingMachines"])
            device_count = parse_fw_versions.parse_file(file=file, full_version_info_file=version_file)
            # update_html(counter=actual_count, device_count=device_count, filepath=sys.argv[1] if len(sys.argv) > 1 else None)
            create_json(counter=actual_count, device_count=device_count, filepath=json_file)
        else:
            print(f"Error. Result code is {response['ResultCode']}")
