# Rubik's Cube OLL Map

Django app for mapping the OLL (Orientation of the Last Layer) cases.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env   # then set DJANGO_SECRET_KEY
uv run python manage.py migrate
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/ (admin at `/admin/`; create a user with
`uv run python manage.py createsuperuser`).

## Layout

- `config/` – project settings, root URLs, WSGI/ASGI
- `oll/` – the main app
- `templates/` – project-wide templates (`base.html`)
- `static/` – project-wide static files
