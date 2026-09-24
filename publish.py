import os
import shlex
import subprocess
import sys

from dotenv import load_dotenv

import output

RSYNC_TIMEOUT = 60


def build_command(paths: list[str], target: str, ssh_key: str = None) -> list[str]:
    ssh = ["ssh", "-o", "BatchMode=yes"]
    if ssh_key:
        ssh += ["-i", os.path.expanduser(ssh_key)]
    return ["rsync", "-t", "--chmod=F644", "--delay-updates", f"--timeout={RSYNC_TIMEOUT}", "-e", shlex.join(ssh), *paths, target]


if __name__ == "__main__":
    load_dotenv(override=True)

    files = sys.argv[1:]
    if not files:
        print("Usage: publish.py FILE [FILE ...]")
        sys.exit(2)

    target = os.getenv("PUBLISH_TARGET")
    if not target:
        print("Error. PUBLISH_TARGET is not set")
        sys.exit(1)

    source_dir = output.output_dir()
    paths = [os.path.join(source_dir, name) for name in files]
    missing = [name for name, path in zip(files, paths) if not os.path.isfile(path)]
    if missing:
        print(f"Error. Not found in {source_dir}: {', '.join(missing)}")
        sys.exit(1)

    try:
        result = subprocess.run(build_command(paths, target, os.getenv("PUBLISH_SSH_KEY")), timeout=2 * RSYNC_TIMEOUT)
    except subprocess.TimeoutExpired:
        print("Error. rsync timed out")
        sys.exit(1)
    if result.returncode:
        print(f"Error. rsync exited with code {result.returncode}")
    sys.exit(result.returncode)
