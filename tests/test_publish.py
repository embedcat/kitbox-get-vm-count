import shlex

import publish


def test_build_command_without_key():
    cmd = publish.build_command(["/out/data.json", "/out/version_info.txt"], "kitbox@vps:")
    assert cmd[0] == "rsync"
    assert cmd[-3:] == ["/out/data.json", "/out/version_info.txt", "kitbox@vps:"]
    assert "--delay-updates" in cmd
    ssh = shlex.split(cmd[cmd.index("-e") + 1])
    assert ssh == ["ssh", "-o", "BatchMode=yes"]


def test_build_command_with_key_quotes_path():
    cmd = publish.build_command(["/out/server_status.json"], "kitbox@vps:", ssh_key="/home/kit/my keys/publish")
    ssh = shlex.split(cmd[cmd.index("-e") + 1])
    assert ssh == ["ssh", "-o", "BatchMode=yes", "-i", "/home/kit/my keys/publish"]
