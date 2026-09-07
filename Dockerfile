FROM python:3.12-slim

ARG RMV_VERSION=1.1.0

LABEL org.opencontainers.image.title="RogueMediaValidator" \
      org.opencontainers.image.description="Provider-neutral torrent payload validation and protection" \
      org.opencontainers.image.source="https://github.com/RogueAssassin/RogueMediaValidator" \
      org.opencontainers.image.url="https://github.com/RogueAssassin/RogueMediaValidator" \
      org.opencontainers.image.version="${RMV_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 10001 rmv

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY --chown=rmv:rmv app ./app

RUN mkdir -p /data && chown rmv:rmv /data

USER rmv
EXPOSE 7811
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7811/healthz', timeout=3).read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7811", "--no-access-log"]
