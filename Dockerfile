# Multi-stage: builder wheels the package, runtime adds Chrome + installs it.
FROM python:3.14-slim-bookworm AS builder

WORKDIR /build
COPY pyproject.toml README.md outlook.py ./
RUN python -m pip install --upgrade pip \
    && python -m pip wheel -w /wheels .

FROM python:3.14-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Google Chrome (stable) for Selenium. Version intentionally unpinned:
# Chrome releases weekly; Selenium Manager pairs the driver automatically.
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget gnupg ca-certificates fonts-liberation \
    && wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y --no-install-recommends /tmp/google-chrome.deb \
    && rm -f /tmp/google-chrome.deb \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 10001 appuser

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-index --find-links=/wheels python-selenium-outlook \
    && rm -rf /wheels
COPY outlook.py ./

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import outlook; print('ok')"

ENTRYPOINT ["python", "outlook.py"]
