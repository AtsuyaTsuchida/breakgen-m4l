# Debug sink: v8 POSTs log lines here when DEBUG_URL is set in breakgen.js.
import http.server, urllib.parse, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = self.rfile.read(n).decode("utf-8", "replace")
        msg = urllib.parse.parse_qs(body).get("m", [body])[0]
        with open(sys.argv[1], "a") as f: f.write(msg + "\n")
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", 8765), H).serve_forever()
