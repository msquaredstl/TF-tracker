# Transformers Collection Tracker — Complete

Normalized FastAPI + SQLModel + SQLite app with importers and seeders, plus your attribute CSVs.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # fill in your remote MySQL credentials or keep the SQLite default
python -m app.db.session --check-connection  # uses the credentials from .env by default
uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```

> Need to confirm a set of credentials before updating `.env`? Run `python -m app.db.session --check-connection --url "mysql+pymysql://username:password@host:3306/database"` to validate connectivity on demand.

## Seed data
### Option A — YAML (from `seeds/seed.yaml`)
```bash
python -m app.importers.seed_from_yaml --path seeds/seed.yaml
```

### Option B — Directly from CSVs (uses files under `attributes/`)
```bash
python -m app.importers.seed_from_csvs --dir attributes
```

## Import your main sheet (CSV export)
```bash
python -m app.importers.import_csv /path/to/your/Sheet1.csv
```

Notes:
- Configure your remote database credentials in `.env` first; the importer will
  refuse to run against the local SQLite fallback unless you pass
  `--allow-sqlite`.
- Characters field supports comma/semicolon; add `|primary` after one name.
- Lines auto-link to Companies when both names are present.
- All seeders/importers are idempotent (safe to re-run).

## Django frontend/backend
Run the Django project located under `django_site/` if you prefer a traditional Django stack
that shares the same SQLite/SQLModel database:

```bash
cd django_site
python manage.py runserver
# open http://127.0.0.1:8000
```

The Django models reuse the existing tables, so your data stays in sync regardless of whether
you use the FastAPI or Django entry points.
