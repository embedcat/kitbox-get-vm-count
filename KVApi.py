from dataclasses import dataclass
import hashlib
import json
import time

import requests


GET_MODEMS_ENDPOINT = "https://api2.kit-invest.ru/APIService.svc/GetModems"
GET_VENDING_MACHNES_ENDPOINT = "https://api2.kit-invest.ru/APIService.svc/GetVendingMachines"
GET_VENDING_MACHINE_BY_ID_ENDPOINT = "https://api2.kit-invest.ru/APIService.svc/GetVendingMachineById"
GET_VM_STATES_ENDPOINT = "https://api2.kit-invest.ru/APIService.svc/GetVMStates"


@dataclass
class APIClient:
    company_id: int
    user_login: str
    user_password: str


class KVApi():
    def __init__(self, client: APIClient) -> None:
        self.client = client

    def get_vm_states(self, file_path_to_dump: str = None) -> json:
        auth = self._make_auth()
        # filter = make_filter(up_date="20.12.2023 15:41:08", to_date="21.12.2023 13:59:00")
        body = self._make_body(auth=auth)
        response = self._send_request(url=GET_VM_STATES_ENDPOINT, body=body, save_to_file=file_path_to_dump)
        return response

    def _send_request(self, url: str, body: str, save_to_file: str = None) -> json:
        print("Sending request ...")
        r = requests.post(url=url, data=body)
        print(f"Response received, status code: {r.status_code}")
        response = r.json()
        if save_to_file:
            with open(save_to_file, "w") as f:
                json.dump(response, f, indent=4)
        return response

    def _make_auth(self) -> dict:
        request_id = int(time.time())
        sign = hashlib.md5(
            f"{str(self.client.company_id)}{str(self.client.user_password)}{str(request_id)}".encode()
        ).hexdigest()
        auth = {
            "CompanyId": self.client.company_id,
            "RequestId": request_id,
            "UserLogin": self.client.user_login,
            "Sign": sign,
        }
        return auth

    def _make_filter(self, up_date: str, to_date: str, company_id: int = None, vm_id: int = None) -> dict:
        filter = {"UpDate": up_date, "ToDate": to_date}
        if company_id:
            filter["CompanyId"] = company_id
        if vm_id:
            filter["VendingMachineId"] = vm_id

        return filter

    def _make_id(self, id: int) -> dict:
        return {"VendingMachineId": id}

    def _make_body(self, auth=None, filter=None, id=None) -> str:
        body = {}
        if auth:
            body["Auth"] = auth
        if filter:
            body["Filter"] = filter
        if id:
            body["Id"] = int(id)

        body = json.dumps(body, indent=4)
        print(body)
        return body
