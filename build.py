#!/usr/bin/env python3
"""Build the Mad Lab Defence Wiki page.

Reads data/live.json (refreshed daily), data/nato.json, data/static.json and the
world map, validates them, and writes dist/index.html for publishing.
Usage: python3 build.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def check_live(live):
    errors = []
    for key in ("updatedAt", "situation", "news", "press", "readings", "toolkit"):
        if key not in live:
            errors.append(f"live.json is missing '{key}'")
    for i, n in enumerate(live.get("news", [])):
        for k in ("pri", "region", "date", "title", "summary", "source", "url"):
            if k not in n:
                errors.append(f"news[{i}] is missing '{k}'")
        if n.get("pri") not in (1, 2, 3, 4):
            errors.append(f"news[{i}] has pri {n.get('pri')!r}; use 1-4")
    ids = set()
    for i, p in enumerate(live.get("press", [])):
        for k in ("id", "org", "type", "titleNo", "title", "tldr", "summary", "startup", "url"):
            if k not in p:
                errors.append(f"press[{i}] is missing '{k}'")
        pid = p.get("id", "")
        if pid in ids or not pid.replace("-", "").isalnum():
            errors.append(f"press[{i}] id {pid!r} must be unique, ASCII letters, digits and hyphens")
        ids.add(pid)
    for i, r in enumerate(live.get("readings", [])):
        if not r.get("tldr"):
            errors.append(f"readings[{i}] is missing 'tldr' (one-line bottom line)")
    for i, f in enumerate(live.get("funding", [])):
        for k in ("id", "title", "funder", "status", "amount", "who", "tldr", "url"):
            if not f.get(k):
                errors.append(f"funding[{i}] is missing '{k}'")
        if f.get("status") not in ("open", "rolling", "upcoming", "closed"):
            errors.append(f"funding[{i}] status must be open, rolling, upcoming or closed")
        if f.get("status") == "open" and not f.get("deadline"):
            errors.append(f"funding[{i}] is open but has no deadline")
    for i, t in enumerate(live.get("tenders", [])):
        for k in ("id", "title", "buyer", "value", "kind", "tldr", "url"):
            if not t.get(k):
                errors.append(f"tenders[{i}] is missing '{k}'")
    for i, e in enumerate(live.get("calendar", [])):
        for k in ("id", "title", "start", "end", "city", "country", "kind", "org", "tldr", "url"):
            if not e.get(k):
                errors.append(f"calendar[{i}] is missing '{k}'")
        if e.get("start", "") > e.get("end", ""):
            errors.append(f"calendar[{i}] starts after it ends")
    for i, s in enumerate(live.get("situation", [])):
        if s.get("level") not in ("elevated", "war", "calm"):
            errors.append(f"situation[{i}] level must be elevated, war or calm")
    return errors


def main():
    live = load("data/live.json")
    errors = check_live(live)
    if errors:
        print("Build stopped:\n  " + "\n  ".join(errors))
        sys.exit(1)
    data = {
        "live": live,
        "nato": load("data/nato.json"),
        "static": load("data/static.json" if (ROOT / "data/static.json").exists() else "data/static.example.json"),
        "insights": load("data/insights.json"),
        "geo": load("vendor/countries-110m.json"),
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (ROOT / "template.html").read_text(encoding="utf-8")
    marker = "/*__DATA__*/null"
    if marker not in html:
        print("Build stopped: template.html has no data marker")
        sys.exit(1)
    out = ROOT / "dist" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html.replace(marker, blob), encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB), "
          f"{len(live['news'])} news, {len(live['press'])} press, {len(live['readings'])} readings")


if __name__ == "__main__":
    main()
