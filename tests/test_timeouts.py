import socket
import threading
import time

import check_servers


def _silent_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def accept_loop():
        try:
            conn, _ = srv.accept()
            time.sleep(5)
            conn.close()
        except OSError:
            pass

    threading.Thread(target=accept_loop, daemon=True).start()
    return srv, port


def test_check_services_api_times_out(monkeypatch):
    srv, port = _silent_server()
    try:
        monkeypatch.setattr(check_servers, "SERVICES_API_TIMEOUT", (0.2, 0.2))
        start = time.monotonic()
        result = check_servers.check_services_api(urls=[f"http://127.0.0.1:{port}/"])
        elapsed = time.monotonic() - start
        assert result[0]["ok"] is False
        assert elapsed < 5
    finally:
        srv.close()
