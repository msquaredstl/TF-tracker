# Transformers Collection Tracker — Complete

Normalized FastAPI + SQLModel + SQLite app with importers and seeders, plus your attribute CSVs.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```

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
