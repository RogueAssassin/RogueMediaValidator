FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 10001 rmv
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
RUN mkdir -p /data && chown -R rmv:rmv /app /data
USER rmv
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)"
CMD ["sh","-c","uvicorn app.main:app --host ${RMV_HOST:-0.0.0.0} --port ${RMV_PORT:-8080}"]
