# Python Selenium — Outlook

![CI](https://github.com/mortogo321/python-selenium-outlook/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Selenium](https://img.shields.io/badge/selenium-4.49.0-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Selenium browser-automation demo: drives Chrome through the Outlook web login
flow and lists inbox message subjects. Showcases stealth Chrome configuration,
resilient explicit waits, and DOM scraping of a dynamic web UI — packaged as a
typed, tested, Docker-ready Python project.

## Features

- Headless Chrome with anti-detection tweaks (automation flags stripped,
  `navigator.webdriver` masked, modern user agent)
- Resilient `WebDriverWait` flows throughout — no fixed sleeps except short
  human-like pacing delays
- Full login flow: email → password → optional "Stay signed in?" → Inbox →
  subject scrape
- Credentials via env (`OUTLOOK_EMAIL` / `OUTLOOK_PASSWORD`) or interactive
  prompts — never written to disk or logged
- Typed (`mypy --strict`), linted (`ruff`), and unit-tested with the browser
  fully mocked (21 tests, no real Chrome needed for CI)
- Multi-stage Docker image with Chrome + non-root user + healthcheck
- CI: lint + typecheck + test + Docker build; Dependabot weekly

## Quickstart

Requires Python 3.12+ and Chrome (Selenium Manager downloads the matching
chromedriver automatically — no manual install needed).

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

Run it (prompts for credentials when env vars are unset):

```bash
python outlook.py
# or: outlook-demo
```

With env credentials (note: prefer a test account; see disclaimer):

```bash
OUTLOOK_EMAIL="you@outlook.com" OUTLOOK_PASSWORD="..." python outlook.py
```

| Env var            | Default                          | Description                              |
| ------------------ | -------------------------------- | ---------------------------------------- |
| `OUTLOOK_EMAIL`    | _(prompt)_                       | Login email (else `input()` prompt)      |
| `OUTLOOK_PASSWORD` | _(prompt)_                       | Password (else `getpass` prompt)         |
| `OUTLOOK_HEADLESS` | `1`                              | `0`/`false`/`no` runs headed Chrome      |
| `OUTLOOK_TIMEOUT`  | `20`                             | Explicit-wait timeout in seconds         |
| `OUTLOOK_LOGIN_URL`| `https://outlook.live.com/owa/`  | Entry URL (override for regional hosts)  |
| `OUTLOOK_USER_AGENT` | Chrome 131 on Windows          | Override the automation user agent       |

## Docker

```bash
docker build -t python-selenium-outlook .
docker run --rm -it \
  -e OUTLOOK_EMAIL="you@outlook.com" \
  -e OUTLOOK_PASSWORD="..." \
  python-selenium-outlook
```

## Project structure

```text
outlook.py              # automation: options → driver → login → inbox → subjects + CLI
tests/test_outlook.py   # 21 unit tests (selenium mocked, no browser needed)
pyproject.toml          # PEP 621 packaging, ruff, mypy strict, pytest config
Dockerfile              # multi-stage (builder wheels + runtime with Chrome, non-root)
.github/workflows/ci.yml   # lint + typecheck + test + docker build
.github/dependabot.yml     # weekly pip/docker/actions updates
Makefile                # install / lint / typecheck / test / build / docker
```

## Quality gates

```bash
make lint       # ruff check + format check
make typecheck  # mypy --strict
make test       # pytest (21 tests)
make build      # pip wheel
make docker     # docker build
```

## Security notes

- Removed the original demo's insecure flags (`--disable-web-security`,
  `--allow-running-insecure-content`).
- `--no-sandbox` is kept because Chrome needs it when running as root inside
  Docker; outside containers prefer a non-root user.
- Secrets only come from env or interactive prompts and never appear in logs;
  `getpass` keeps password entry off-screen.

## Disclaimer

Automating the Outlook login UI can trigger Microsoft bot defenses, CAPTCHAs,
or MFA challenges, and may violate Microsoft's Terms of Service for your
account type. Use a dedicated test account, expect selectors to drift as
Microsoft ships UI changes, and prefer the official
[Microsoft Graph API](https://learn.microsoft.com/graph/) for production
mailbox access.

## Sep-2026 refresh

- Fixed the empty login URL bug (now `https://outlook.live.com/owa/`,
  overridable via `OUTLOOK_LOGIN_URL`)
- Refactored the top-level script into importable, typed functions with no
  import-time side effects; added `run()` / `main()` with exit codes
- Pinned Selenium 4.49.0, modernized user agent (Chrome 131), dropped insecure
  Chrome flags, `--headless=new`
- Added PEP 621 packaging, `mypy --strict`, `ruff`, 21 mocked pytest tests,
  multi-stage Docker, CI, Dependabot, and MIT license

## License

MIT — see [LICENSE](LICENSE).
