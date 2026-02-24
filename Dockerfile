FROM python:3.12-slim AS build

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv sync --system --no-dev

COPY . .

RUN DATABASE_URL=sqlite:///app/db.sqlite3 \
    python manage.py collectstatic --noinput

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=fattyurl.settings \
    DATABASE_URL=sqlite:///app/db.sqlite3

COPY --from=build /usr/local/lib /usr/local/lib
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /app /app

EXPOSE 8000

CMD ["gunicorn", "fattyurl.wsgi:application", "--bind", "0.0.0.0:8000"]
