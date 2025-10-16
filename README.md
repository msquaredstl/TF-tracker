# Transformers Collection Tracker — Complete

Normalized FastAPI + SQLModel + SQLite app with importers and seeders, plus your attribute CSVs.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # populate it with the provided remote MySQL credentials
python -m app.db.session --check-connection
uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```

> Need to confirm the remote credentials before updating `.env`? Run `python -m app.db.session --check-connection --url "mysql+pymysql://5uqnyG9pM5Hb:FjppZC7QgJQc@50.62.201.246:3306/ZPmPR8yPjSuY"` to validate connectivity on demand.

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
- Characters field supports comma/semicolon; add `|primary` after one name.
- Lines auto-link to Companies when both names are present.
- All seeders/importers are idempotent (safe to re-run).
