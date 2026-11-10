# Mad Lab Defence Wiki

Onboarding wiki for the defence startups in AI Mad Lab: a daily situation report (Norway, the Nordics, Ukraine, Europe), a clickable NATO map, defence-sector news, press releases from FD, Forsvaret and FMA with the startup angle, an events calendar, a reading list and the team's network.

## Where to read it

- **Team (editable network):** the claude.ai artifact. Ask the owner for access.
- **Partners:** the password-protected copy on GitHub Pages. Ask the owner for the password.

## How it is built

| File | What it is |
|---|---|
| `template.html` | The page (HTML, CSS and JS). |
| `data/live.json` | Content refreshed every morning at 08:00: situation, news, press releases, readings, events calendar. |
| `data/nato.json` | NATO 2026 figures per ally (source: NATO, July 2026). |
| `data/static.json` | **Private, not committed.** Network contacts and meeting notes. `data/static.example.json` shows the shape. |
| `vendor/` | World map geometry (world-atlas, ISC licence). |
| `build.py` | Validates the data and writes `dist/index.html` (plain, for claude.ai). |
| `site.py` | Encrypts that build into `docs/index.html` for GitHub Pages (AES-256-GCM, key from the password via PBKDF2). |

```bash
python3 build.py && python3 site.py
```

The site password comes from the `WIKI_PASSWORD` environment variable or a local, git-ignored `.site-password` file. Changing the password means re-running `site.py` and sharing the new password.
