"""Verification runner for Phase 0.
Launches a test Ollama endpoint, invokes main.py with OLLAMA_HOST set, and validates the exact output.
"""

import json
import os
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class MockOllama(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/tags":
            payload = {
                "models": [
                    {"name": "gemma4:12b", "model": "gemma4:12b"},
                    {"name": "gemma4:e4b", "model": "gemma4:e4b"}
                ]
            }
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass

def main():
    server = HTTPServer(("127.0.0.1", 11435), MockOllama)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    env = os.environ.copy()
    env["OLLAMA_HOST"] = "http://127.0.0.1:11435"

    result = subprocess.run(
        [sys.executable, "main.py"],
        env=env,
        capture_output=True,
        text=True
    )

    print("--- Output from main.py ---")
    print(result.stdout)
    if result.stderr:
        print("--- Stderr ---")
        print(result.stderr)

    assert result.returncode == 0, f"Expected returncode 0, got {result.returncode}"
    assert "Loaded configuration for Boss." in result.stdout
    assert "Configured brain: gemma4:12b" in result.stdout
    assert "Ollama is ready" in result.stdout
    print("Verification PASSED: main.py started, read config, and printed 'Ollama is ready'.")

    server.shutdown()

if __name__ == "__main__":
    main()
