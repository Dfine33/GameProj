import json
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai.policy import SimplePolicy
from simulation.loop import SimulationLoop

ROOT = os.path.dirname(__file__)

class StateHolder:
    def __init__(self, loop):
        self.loop = loop
        self.paused = False
        self.speed = 1.0
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        while True:
            if not self.paused:
                self.loop.step()
            time.sleep(max(0.0, 0.016 / max(0.1, self.speed)))

class Handler(SimpleHTTPRequestHandler):
    holder = None

    def translate_path(self, path):
        if path.startswith('/api/'):
            return path
        p = path.strip('/')
        if p == '':
            p = 'index.html'
        return os.path.join(ROOT, p)

    def do_GET(self):
        if self.path.startswith('/api/state'):
            body = json.dumps(self.holder.loop.state.serialize()).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/control'):
            length = int(self.headers.get('Content-Length','0'))
            raw = self.rfile.read(length).decode('utf-8') if length > 0 else '{}'
            try:
                data = json.loads(raw)
            except Exception:
                data = {}
            cmd = data.get('cmd')
            if cmd == 'pause':
                self.holder.paused = True
            elif cmd == 'resume':
                self.holder.paused = False
            elif cmd == 'speed':
                v = float(data.get('value', 1.0))
                self.holder.speed = max(0.1, min(3.0, v))
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{}')
            return
        self.send_response(404)
        self.end_headers()

def main():
    loop = SimulationLoop(SimplePolicy(), renderer=None)
    holder = StateHolder(loop)
    Handler.holder = holder
    holder.start()
    server = HTTPServer(('localhost', 8000), Handler)
    server.serve_forever()

if __name__ == '__main__':
    main()