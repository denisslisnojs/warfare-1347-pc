import socket, json, sys
def send(cmd, params=None, timeout=600):
    s = socket.create_connection(("127.0.0.1", 9876), timeout=timeout)
    s.sendall(json.dumps({"type": cmd, "params": params or {}}).encode())
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk: break
        buf += chunk
        try:
            r = json.loads(buf.decode()); break
        except ValueError: continue
    s.close(); return r
if __name__ == "__main__":
    cmd = sys.argv[1]
    params = {"code": open(sys.argv[2], encoding="utf-8").read()} if len(sys.argv) > 2 else None
    print(json.dumps(send(cmd, params), ensure_ascii=False)[:4000])
