from datetime import datetime
import os

from KVApi import MSK

DEFAULT_OUTPUT_DIR = "data"


def output_dir() -> str:
    script_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_path, os.getenv("OUTPUT_DIR") or DEFAULT_OUTPUT_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def timestamps(now: datetime = None) -> dict:
    now = now or datetime.now(MSK)
    return {
        "updated_datetime": now.strftime("%d/%m/%Y %H:%M:%S"),
        "updated_ts": now.isoformat(timespec="seconds"),
    }


def write_atomic(path: str, text: str) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        f.write(text)
    os.replace(tmp_path, path)
