# Mad Lab Defence Wiki

Onboarding wiki for the defence startups in AI Mad Lab: a daily situation report (Norway, the Nordics, Ukraine, Europe), a clickable NATO map, defence-sector news, press releases from FD, Forsvaret and FMA with the startup angle, an events calendar, a reading list and the team's network.

## Where to read it

- **Team (editable network):** the claude.ai artifact. Ask the owner for access.
- **Partners:** the copy on GitHub Pages.

Both copies ask for the same password. The wiki's data is stored encrypted inside the page and only decrypted in the visitor's browser.

## How it is built

| File | What it is |
|---|---|
| `template.html` | The page (HTML, CSS and JS). |
| `data/live.json` | Content refreshed every morning at 08:00: situation, news, press releases, readings, events calendar. |
| `data/nato.json` | NATO 2026 figures per ally (source: NATO, July 2026). |
| `data/static.json` | **Private, not committed.** Network contacts and meeting notes. `data/static.example.json` shows the shape. |
| `vendor/` | World map geometry (world-atlas, ISC licence). |
| `build.py` | Validates the data and writes `dist/index.html` with the data encrypted (AES-256-GCM, key from the password via PBKDF2). Published to claude.ai. |
| `site.py` | Wraps that page into `docs/index.html` for GitHub Pages. |

```bash
python3 build.py && python3 site.py
```

The password comes from the `WIKI_PASSWORD` environment variable or a local, git-ignored `.site-password` file. Changing it means re-running both scripts, republishing, and sharing the new password.
