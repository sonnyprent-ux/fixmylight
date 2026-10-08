FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    FIXMYLIGHT_DB=/data/fixmylight.sqlite3 \
    FIXMYLIGHT_SCHEDULER=true \
    PORT=8000

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY fixmylight ./fixmylight
RUN pip install --no-cache-dir ".[server,ai]" && mkdir -p /data && useradd -m app && chown app /data
USER app
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/healthz')"
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --access-logfile - 'fixmylight.app:create_app()'"]
