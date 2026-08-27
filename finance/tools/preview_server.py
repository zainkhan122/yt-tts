#!/usr/bin/env python3
"""preview_server.py — watch images and videos in the live preview.
Binds 0.0.0.0 so the platform can proxy it.
Usage: python3 tools/preview_server.py [port]
"""
import html, http.server, os, socketserver, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
MEDIA = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
         ".mp4", ".webm", ".mov", ".mp3", ".wav"}

def collect():
    items = []
    for p in sorted(ROOT.rglob("*")):
        if p.suffix.lower() in MEDIA and "/.git/" not in str(p):
            rel = p.relative_to(ROOT).as_posix()
            items.append(rel)
    return items

INDEX = """<!doctype html>
<html><head><meta charset="utf-8">
<title>THRESHOLD preview</title>
<style>
body{margin:0;background:#0B1F33;color:#F4F1EA;font-family:system-ui,sans-serif}
h1{font-size:20px;padding:16px 20px;margin:0;border-bottom:1px solid #1C3348;color:#F4C15D}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;padding:16px}
.card{background:#1C3348;border-radius:10px;overflow:hidden}
.card h2{font-size:12px;margin:0;padding:8px 10px;color:#8AA0B5;word-break:break-all}
img,video{display:block;width:100%;background:#000}
.empty{padding:40px;color:#8AA0B5}
</style></head><body>
<h1>THRESHOLD — preview ({n} files)</h1>
{body}
</body></html>"""

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            items = collect()
            if not items:
                body = '<p class="empty">No media yet. Run tools/motion_kit.py sample</p>'
            else:
                cards = []
                for rel in items:
                    q = urllib.parse.quote(rel)
                    if Path(rel).suffix.lower() in {".mp4", ".webm", ".mov"}:
                        media = f'<video controls src="/{q}"></video>'
                    elif Path(rel).suffix.lower() in {".mp3", ".wav"}:
                        media = f'<audio controls src="/{q}"></audio>'
                    else:
                        media = f'<img src="/{q}" alt="">'
                    cards.append(f'<div class="card"><h2>{html.escape(rel)}</h2>{media}</div>')
                body = '<div class="grid">' + "".join(cards) + "</div>"
            page = INDEX.format(n=len(items), body=body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return
        return super().do_GET()
    def log_message(self, fmt, *args):
        sys.stderr.write("preview: " + (fmt % args) + "\n")

class Reuse(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    os.chdir(ROOT)
    http.server.SimpleHTTPRequestHandler.extensions_map[".js"] = "text/javascript"
    with Reuse(("0.0.0.0", PORT), H) as httpd:
        print(f"THRESHOLD preview on 0.0.0.0:{PORT}  root={ROOT}", flush=True)
        httpd.serve_forever()
