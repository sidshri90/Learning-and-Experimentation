"""Download a pinned copy of HTMX into app/static/vendor/ (run once)."""
import hashlib
import urllib.request
from pathlib import Path

VERSION = "2.0.4"
URL = f"https://cdn.jsdelivr.net/npm/htmx.org@{VERSION}/dist/htmx.min.js"
DEST = Path(__file__).resolve().parent.parent / "app/static/vendor/htmx.min.js"

DEST.parent.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen(URL, timeout=30) as resp:
    data = resp.read()
DEST.write_bytes(data)
print(f"Saved htmx {VERSION} ({len(data):,} bytes) to {DEST}")
print(f"sha256: {hashlib.sha256(data).hexdigest()}")
