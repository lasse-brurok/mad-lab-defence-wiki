#!/usr/bin/env python3
"""Copy the team's live Network contacts into the password-protected page.

The daily refresh exports the claude.ai artifact's "contacts" collection as one
JSON file per contact (ArtifactData list with out_dir), then runs:

    python3 sync_contacts.py <export-folder>/contacts

This writes data/contacts.json (git-ignored, private). build.py encrypts it into
the page, so everyone with the link and the password sees the contacts, while
the live database stays readable only by team members.
"""
import json
import pathlib
import sys
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent
FIELDS = ("name", "org", "role", "cat", "owner", "phone", "email", "link", "note", "createdAt", "updatedAt")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 sync_contacts.py <folder with one JSON file per contact>")
        sys.exit(1)
    folder = pathlib.Path(sys.argv[1])
    files = sorted(folder.glob("*.json"))
    if not files:
        print(f"Stopped: no contact files in {folder}. data/contacts.json was left unchanged.")
        sys.exit(1)
    people = []
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        doc = doc.get("data", doc)  # accept both plain documents and {"id", "data"} wrappers
        if not str(doc.get("name", "")).strip():
            continue
        p = {k: str(doc.get(k, "") or "") for k in FIELDS}
        p["id"] = f.stem
        people.append(p)
    out = ROOT / "data" / "contacts.json"
    out.write_text(json.dumps({"syncedAt": datetime.now().astimezone().replace(microsecond=0).isoformat(),
                               "people": people}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {out}: {len(people)} contacts")


if __name__ == "__main__":
    main()
