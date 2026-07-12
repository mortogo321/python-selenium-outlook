# Python Selenium - Outlook

A small Selenium script demonstrating browser automation patterns against Outlook/Hotmail webmail: stealth Chrome configuration, resilient element waits, and DOM scraping of dynamic web UI.

## What's inside

`outlook.py` drives a Chrome browser through the Outlook web login flow and lists inbox message subjects:

- Launches Chrome in headless mode with anti-bot-detection tweaks (randomized user agent, disabled automation flags, hidden `navigator.webdriver` property).
- Fills in the Microsoft login form (email, then password) and submits it.
- Handles the optional "Stay signed in?" prompt if it appears.
- Opens the Inbox and prints the subject line of each visible message.
- Uses explicit `WebDriverWait` conditions throughout instead of fixed sleeps, with randomized human-like delays between actions.

Credentials are entered interactively at runtime (email via `input()`, password via `getpass`) — nothing is read from or written to a config file, and no secrets are stored in the repo.

## Tech stack

- Python 3.13
- Selenium (Chrome/Chromedriver)

## Quickstart

```bash
python -m venv env
source env/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

Run the script and enter your Outlook/Hotmail credentials when prompted:

```bash
source env/bin/activate
python outlook.py
```

Requires a matching Chromedriver available on `PATH` for your installed version of Chrome.
