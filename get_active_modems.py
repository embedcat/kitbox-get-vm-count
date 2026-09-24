import json
import os
import sys
import parse_fw_versions
import requests
from KVApi import KVApi, APIClient, MSK
from datetime import datetime
from dotenv import load_dotenv


TEMP_FILENAME = "vend_machines.txt"
VERSION_FILENAME = "version_info.txt"
DATA_JSON_FILENAME = "data.json"


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
    client = APIClient(company_id=int(os.getenv("COMPANY_ID")), user_login=os.getenv("USER_LOGIN"), user_password=os.getenv("USER_PASSWORD"))
    api = KVApi(client=client)

    script_path = os.path.dirname(os.path.abspath(__file__))
    file = f"{script_path}/{TEMP_FILENAME}"
    if os.path.exists(file):
        os.remove(file)

    version_file = f"{script_path}/{VERSION_FILENAME}"
    json_file = f"{script_path}/{DATA_JSON_FILENAME}"

    try:
        response = api.get_vm_states(file_path_to_dump=file)
    except requests.exceptions.JSONDecodeError as e:
        print(f"Error. Response is not valid JSON: {e}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Error. Request failed: {e}")
        sys.exit(1)

    if response["ResultCode"] == 0:
        active_vms, invalid_count = parse_fw_versions.filter_active(response["VendingMachines"], datetime.now(MSK))
        if invalid_count:
            print(f"VMs without valid DateTime: {invalid_count}")
        actual_count = len(active_vms)
        device_count = parse_fw_versions.parse_file(vms=active_vms, full_version_info_file=version_file)
        create_json(counter=actual_count, device_count=device_count, filepath=json_file)
    else:
        print(f"Error. Result code is {response['ResultCode']}: {response.get('ErrorMessage')}")
        sys.exit(1)
