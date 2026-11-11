#!/usr/bin/env python3
"""Password protection for the wiki, and the GitHub Pages copy.

build.py calls encrypt_json() so that the wiki's data (news, contacts, notes,
everything) is stored encrypted inside the page: AES-256-GCM with a key derived
from the site password (PBKDF2-SHA256, 600,000 iterations). The page shows a
login screen and decrypts the data in the visitor's browser. The same page is
published to claude.ai and to GitHub Pages.

Running this script writes docs/index.html for GitHub Pages: the already
protected dist/index.html wrapped in a full HTML document.

The password is read from the WIKI_PASSWORD environment variable or from the
.site-password file next to this script (git-ignored). Never commit it.
Usage: python3 build.py && python3 site.py
"""
import base64
import json
import os
import pathlib
import secrets
import sys

ROOT = pathlib.Path(__file__).resolve().parent
ITERATIONS = 600_000

SKELETON_HEAD = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<meta name="robots" content="noindex,nofollow">'
    "<style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);"
    "padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;padding:0;font:14px -apple-system,"
    "BlinkMacSystemFont,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>"
)


def password(required=True):
    pw = os.environ.get("WIKI_PASSWORD")
    if not pw:
        f = ROOT / ".site-password"
        if f.exists():
            pw = f.read_text(encoding="utf-8").strip()
    if not pw or len(pw) < 8:
        if not required:
            return None
        print("Stopped: set WIKI_PASSWORD or put a password of 8+ characters in .site-password")
        sys.exit(1)
    return pw


def salt():
    # A stable, public salt keeps "Remember on this device" working across daily rebuilds.
    f = ROOT / "site.salt"
    if not f.exists():
        f.write_text(base64.b64encode(secrets.token_bytes(16)).decode())
    return base64.b64decode(f.read_text().strip())


def encrypt_json(text, pw):
    """Encrypt a JSON string; returns the {"enc": {...}} object the page's login screen expects."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    s, iv = salt(), secrets.token_bytes(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=s, iterations=ITERATIONS).derive(pw.encode())
    ct = AESGCM(key).encrypt(iv, text.encode("utf-8"), None)
    enc = lambda b: base64.b64encode(b).decode()
    return {"enc": {"salt": enc(s), "iv": enc(iv), "iter": ITERATIONS, "ct": enc(ct)}}


def main():
    src = ROOT / "dist" / "index.html"
    if not src.exists():
        print("Stopped: run build.py first")
        sys.exit(1)
    page = src.read_text(encoding="utf-8")
    if '{"enc":' not in page:
        print("Stopped: dist/index.html is not encrypted. Add .site-password and run build.py again.")
        sys.exit(1)
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(SKELETON_HEAD + page + "</body></html>", encoding="utf-8")
    (ROOT / "docs" / ".nojekyll").write_text("")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB, data encrypted)")


if __name__ == "__main__":
    main()
