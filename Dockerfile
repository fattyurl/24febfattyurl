FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY .python-version .
COPY uv.lock .
COPY pyproject.toml .
COPY runtime.txt .
RUN uv sync --no-dev

COPY . .
RUN uv run manage.py collectstatic --noinput
EXPOSE 8000

CMD ["gunicorn", "fattyurl.wsgi:application", "--bind", "0.0.0.0:8000"]
