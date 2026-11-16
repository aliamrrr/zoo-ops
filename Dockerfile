# Zoo Ops in a container: nothing to install but Docker.
#   docker compose up                               play, with your files mounted (see compose.yaml)
#   docker build -t zoo-ops . && docker run --rm -p 8000:8000 zoo-ops
FROM python:3.15-slim

LABEL org.opencontainers.image.title="Zoo Ops" \
      org.opencontainers.image.description="Learn backend system design patterns by keeping a zoo alive." \
      org.opencontainers.image.source="https://github.com/aliamrrr/zoo-ops" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ZOO_HOST=0.0.0.0 \
    ZOO_NO_BROWSER=1 \
    ZOO_STATE_DIR=/home/zoo/state

WORKDIR /app
RUN useradd --create-home --uid 10001 zoo \
    && mkdir /home/zoo/state \
    && chown zoo /home/zoo/state

# Dependencies first: this layer is reused until pyproject.toml changes.
COPY pyproject.toml README.md LICENSE ./
COPY zoo ./zoo
RUN pip install --editable .

COPY levels ./levels
COPY hard ./hard
COPY hardpp ./hardpp

USER zoo
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"

# Python is PID 1 and receives SIGTERM directly; uvicorn then drains for up to 20 s.
ENTRYPOINT ["python", "-m", "zoo"]
CMD ["play", "--no-reload"]
