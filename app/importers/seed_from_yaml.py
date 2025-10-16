import argparse, sys, yaml
from pathlib import Path
from sqlmodel import Session, select
from app.db.session import engine, init_db
from app.models import Faction, Company, Line, Series, ItemType, Category, Vendor, Team, Character

def get_or_create_by_name(session: Session, model, name: str):
    name = name.strip()
    obj = session.exec(select(model).where(model.name == name)).first()
    if obj: return obj
    obj = model(name=name)
    session.add(obj); session.commit(); session.refresh(obj)
    return obj

def seed(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    init_db()
    with Session(engine) as session:
        for n in data.get("factions", []):
            get_or_create_by_name(session, Faction, n)
        for c in data.get("companies", []):
            comp = get_or_create_by_name(session, Company, c.get("name",""))
            for ln in c.get("lines",[]) or []:
                line = get_or_create_by_name(session, Line, ln)
                if line and comp and line.company_id is None:
                    line.company_id = comp.id
                    session.add(line); session.commit()
        for n in data.get("series", []):
            get_or_create_by_name(session, Series, n)
        for n in data.get("types", []):
            get_or_create_by_name(session, ItemType, n)
        for n in data.get("categories", []):
            get_or_create_by_name(session, Category, n)
        for n in data.get("vendors", []):
            get_or_create_by_name(session, Vendor, n)
        for n in data.get("teams", []):
            get_or_create_by_name(session, Team, n)
        for c in data.get("characters", []):
            nm = (c.get("name") or "").strip()
            if not nm: continue
            char = session.exec(select(Character).where(Character.name == nm)).first() or Character(name=nm)
            fac = (c.get("faction") or "").strip()
            if fac:
                f = get_or_create_by_name(session, Faction, fac)
                char.faction_id = f.id
            session.add(char); session.commit()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="seeds/seed.yaml")
    args = ap.parse_args()
    p = Path(args.path)
    if not p.exists():
        print(f"Seed file not found: {p}", file=sys.stderr); sys.exit(2)
    seed(p); print("Seed complete.")

if __name__ == "__main__":
    main()
