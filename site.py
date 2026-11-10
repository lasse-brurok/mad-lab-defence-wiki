#!/usr/bin/env python3
"""Build the password-protected public copy of the wiki for GitHub Pages.

Reads dist/index.html (run build.py first), wraps it in a full HTML document,
encrypts it with AES-256-GCM using a key derived from the site password
(PBKDF2-SHA256, 600,000 iterations), and writes docs/index.html: a small
login page that decrypts the wiki in the visitor's browser.

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

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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

LOGIN = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Mad Lab Defence Wiki</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,600..800&family=Public+Sans:wght@400;600&display=swap">
<style>
:root{--bg:#0f1c26;--card:#14202a;--ink:#e6edf2;--muted:#9fb0bd;--line:#253543;--signal:#f0a35e;--war:#f08077;color-scheme:dark}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Public Sans",system-ui,sans-serif;display:grid;place-items:center;padding:24px max(16px,env(safe-area-inset-left))}
form{width:min(420px,100%);display:grid;gap:14px;background:var(--card);border:1px solid var(--line);padding:28px}
.eyebrow{font:600 11.5px ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--signal)}
h1{margin:0;font:800 40px/1 "Archivo","Arial Narrow",sans-serif;font-stretch:78%;text-transform:uppercase}
p{margin:0;color:var(--muted);font-size:15px}
label{display:grid;gap:6px;font-size:13px;font-weight:600;color:var(--muted)}
input[type=password]{font:inherit;font-size:16px;padding:10px 12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:3px}
.row{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--muted)}
button{font:600 15px "Public Sans",sans-serif;padding:10px;border:0;border-radius:3px;background:var(--signal);color:#1a1006;cursor:pointer}
button:disabled{opacity:.6;cursor:wait}
.err{color:var(--war);font-size:14px;min-height:1.2em}
input:focus-visible,button:focus-visible{outline:2px solid var(--signal);outline-offset:2px}
</style></head><body>
<form id="f" autocomplete="on">
  <span class="eyebrow">AI Mad Lab · Defence</span>
  <h1>Mad Lab Defence Wiki</h1>
  <p>This page is for AI Mad Lab founders and partners. Enter the password you were given.</p>
  <label for="pw">Password<input id="pw" type="password" autocomplete="current-password" required autofocus></label>
  <label class="row"><input id="remember" type="checkbox"> Remember on this device</label>
  <button id="go" type="submit">Open the wiki</button>
  <div class="err" id="err" role="alert"></div>
</form>
<script>
const P = __PAYLOAD__;
const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
async function keyFrom(pw){
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({name:"PBKDF2", hash:"SHA-256", salt:b64(P.salt), iterations:P.iter}, base, 256));
}
async function open(raw){
  const key = await crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["decrypt"]);
  const html = new TextDecoder().decode(await crypto.subtle.decrypt({name:"AES-GCM", iv:b64(P.iv)}, key, b64(P.ct)));
  document.open(); document.write(html); document.close();
}
const STORE = "mlw-key-" + P.salt;
(async () => { try { const k = localStorage.getItem(STORE); if (k) await open(b64(k)); } catch(_) { try { localStorage.removeItem(STORE); } catch(_) {} } })();
document.getElementById("f").addEventListener("submit", async e => {
  e.preventDefault();
  const btn = document.getElementById("go"), err = document.getElementById("err");
  btn.disabled = true; btn.textContent = "Unlocking…"; err.textContent = "";
  try {
    const raw = await keyFrom(document.getElementById("pw").value);
    if (document.getElementById("remember").checked) { try { localStorage.setItem(STORE, btoa(String.fromCharCode(...raw))); } catch(_) {} }
    await open(raw);
  } catch(_) {
    err.textContent = "That password is not right. Check it and try again.";
    btn.disabled = false; btn.textContent = "Open the wiki";
  }
});
</script>
</body></html>
"""


def password():
    pw = os.environ.get("WIKI_PASSWORD")
    if not pw:
        f = ROOT / ".site-password"
        if f.exists():
            pw = f.read_text(encoding="utf-8").strip()
    if not pw or len(pw) < 8:
        print("Site build stopped: set WIKI_PASSWORD or put a password of 8+ characters in .site-password")
        sys.exit(1)
    return pw


def main():
    src = ROOT / "dist" / "index.html"
    if not src.exists():
        print("Site build stopped: run build.py first")
        sys.exit(1)
    html = SKELETON_HEAD + src.read_text(encoding="utf-8") + "</body></html>"
    # A stable, public salt keeps "Remember on this device" working across daily rebuilds.
    salt_file = ROOT / "site.salt"
    if not salt_file.exists():
        salt_file.write_text(base64.b64encode(secrets.token_bytes(16)).decode())
    salt, iv = base64.b64decode(salt_file.read_text().strip()), secrets.token_bytes(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS).derive(password().encode())
    ct = AESGCM(key).encrypt(iv, html.encode("utf-8"), None)
    enc = lambda b: base64.b64encode(b).decode()
    payload = json.dumps({"salt": enc(salt), "iv": enc(iv), "iter": ITERATIONS, "ct": enc(ct)})
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(LOGIN.replace("__PAYLOAD__", payload), encoding="utf-8")
    (ROOT / "docs" / ".nojekyll").write_text("")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB, encrypted)")


if __name__ == "__main__":
    main()
