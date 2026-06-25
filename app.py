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
            cmd,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            timeout=3000,
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout: команда выполнялась дольше 3000 секунд.", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": f"Ошибка: {e}", "returncode": -1}


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_page(cmd: str = "", res: dict = None) -> str:
    output_block = ""
    rc_color = "#888"

    if res is not None:
        rc_color = "#4ec9b0" if res["returncode"] == 0 else "#f48771"
        parts = []
        if res["stdout"]:
            parts.append(f'<span class="stdout">{escape_html(res["stdout"])}</span>')
        if res["stderr"]:
            parts.append(f'<span class="stderr">{escape_html(res["stderr"])}</span>')
        if not parts:
            parts.append('<span style="color:#888">(нет вывода)</span>')

        output_block = f"""
        <div class="meta">
          $ <span class="cmd">{escape_html(cmd)}</span>
          &nbsp;·&nbsp; exit: <span class="rc">{res['returncode']}</span>
        </div>
        <pre>{''.join(parts)}</pre>
        """

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bash Console</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #1e1e1e; color: #d4d4d4; font-family: 'Courier New', monospace; padding: 24px; min-height: 100vh; }}
    h1 {{ color: #4ec9b0; font-size: 1.2rem; margin-bottom: 16px; }}
    form {{ display: flex; gap: 8px; margin-bottom: 20px; }}
    input[type=text] {{ flex: 1; background: #2d2d2d; border: 1px solid #444; color: #d4d4d4; padding: 8px 12px; font-family: inherit; font-size: 0.95rem; border-radius: 4px; outline: none; }}
    input[type=text]:focus {{ border-color: #4ec9b0; }}
    button {{ background: #4ec9b0; color: #1e1e1e; border: none; padding: 8px 18px; font-family: inherit; font-size: 0.95rem; font-weight: bold; border-radius: 4px; cursor: pointer; }}
    button:hover {{ background: #3daf98; }}
    .meta {{ font-size: 0.8rem; color: #888; margin-bottom: 8px; }}
    .meta .cmd {{ color: #ce9178; }}
    .meta .rc {{ color: {rc_color}; }}
    pre {{ background: #2d2d2d; border: 1px solid #444; border-radius: 4px; padding: 16px; white-space: pre-wrap; word-break: break-all; font-size: 0.9rem; line-height: 1.5; min-height: 60px; max-height: 70vh; overflow-y: auto; }}
    .stdout {{ color: #d4d4d4; }}
    .stderr {{ color: #f48771; }}
  </style>
</head>
<body>
  <h1>⬛ Bash Console</h1>
  <form method="get" action="/">
    <input type="text" name="cmd" value="{escape_html(cmd)}" placeholder="введите команду..." autofocus autocomplete="off" spellcheck="false">
    <button type="submit">Run</button>
  </form>
  {output_block}
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        cmd = params.get("cmd", [""])[0]
        cmd = unquote_plus(cmd)

        res = run_command(cmd) if cmd.strip() else None
        body = build_page(cmd, res).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Bash Console запущен на http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлен.")
