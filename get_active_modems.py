import os
from KVApi import KVApi, APIClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup


def count_vms(vms: list) -> int:
    now = datetime.now()
    return len([elem for elem in vms if now - datetime.strptime(elem["DateTime"], "%d.%m.%Y %H:%M:%S") <= timedelta(weeks=2)])


def update_html(counter: int, filepath: str) -> None:
    with open(filepath) as file:
        html = file.read()
        soup = BeautifulSoup(html, "html.parser")
    tag_counter = soup.find(id="counter")
    tag_counter.string = str(counter)
    tag_updated = soup.find(id="updated")
    tag_updated.string = str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    with open(filepath, "w") as file:
        file.write(str(soup))


if __name__ == "__main__":
    load_dotenv()
    client = APIClient(company_id=os.getenv("COMPANY_ID"), user_login=os.getenv("USER_LOGIN"), user_password=os.getenv("USER_PASSWORD"))
    api = KVApi(client=client)
    response = api.get_vm_states()
    if response and response["ResultCode"] == 0:
        actual_count = count_vms(vms=response["VendingMachines"])
        update_html(counter=actual_count, filepath="index.html")
