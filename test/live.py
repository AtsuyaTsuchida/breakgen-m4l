import socket, json, sys
def q(t, p={}):
    s = socket.create_connection(("127.0.0.1", 9877), timeout=70)
    s.sendall(json.dumps({"type": t, "params": p}).encode()); b = b""
    while True:
        c = s.recv(65536)
        if not c: break
        b += c
        try: return json.loads(b)
        except Exception: pass
if __name__ == "__main__":
    print(json.dumps(q(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}))[:3000])
