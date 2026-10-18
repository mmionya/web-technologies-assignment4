#!/usr/bin/env python3
"""Serve the assignment locally, including its harmless demonstration POST action.

Usage: python3 scripts/serve.py [--port 8000]
Submitted values are discarded. This is a form demo, not a booking service.
"""

from argparse import ArgumentParser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUCCESS = b"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Form submitted | Assignment 4</title>
<style>body{font-family:system-ui,sans-serif;line-height:1.6;margin:0;background:#f4f7f5;color:#16302b}
main{max-width:42rem;margin:10vh auto;padding:2rem}a{color:#0f6b5f}li{margin:.7rem 0}</style>
</head><body><main><h1>Form submitted successfully</h1>
<p>The browser accepted the completed form. This is a local assignment demo:
no real booking or registration has been made, and submitted values are not stored.</p>
<ul><li><a href="/task1.html">Train ticket form</a></li>
<li><a href="/task2.html">Hackathon registration</a></li>
<li><a href="/task3.html">Caf\xc3\xa9 reservation</a></li></ul>
</main></body></html>"""


class AssignmentHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/submit":
            self.send_error(404, "Unknown form action")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid content length")
            return
        if size < 0 or size > 65536:
            self.send_error(413, "Form is too large")
            return
        self.rfile.read(size)  # Discard, without inspecting, echoing or storing values.
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(SUCCESS)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(SUCCESS)

    def log_message(self, format, *args):
        # Avoid accidental logging of form data or query-string values.
        return


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    handler = partial(AssignmentHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Assignment 4: http://127.0.0.1:{args.port}/task1.html", flush=True)
    print("Press Ctrl+C to stop. Submitted values are discarded.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
