import argparse
import csv
import os
from typing import Optional

from sqlmodel import Session, select

from app.db.session import engine, init_db
from app.models import (
    Category,
    Character,
    Company,
    Faction,
    ItemType,
    Line,
    Series,
    Team,
    Vendor,
)


def first_present(headers, candidates):
    lower = {h.lower(): h for h in headers}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def get_or_create_by_name(session: Session, model, name: Optional[str]):
    if not name:
        return None
    name = name.strip()
    if not name:
        return None
    obj = session.exec(select(model).where(model.name == name)).first()
    if obj:
        return obj
    obj = model(name=name)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def load_simple_list(session: Session, filepath: str, model, candidates):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            f.seek(0)
            for line in f:
                name = line.strip().strip(",")
                if name:
                    get_or_create_by_name(session, model, name)
            return
        name_col = first_present(reader.fieldnames, candidates)
        for row in reader:
            name = row.get(name_col, "").strip() if name_col else ""
            if name:
                get_or_create_by_name(session, model, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="attributes")
    args = ap.parse_args()
    base = args.dir
    init_db()
    with Session(engine) as session:
        load_simple_list(
            session,
            os.path.join(base, "faction.csv"),
            Faction,
            ["name", "faction", "faction_name"],
        )
        load_simple_list(
            session,
            os.path.join(base, "series.csv"),
            Series,
            ["series", "name", "series_name", "media", "source"],
        )
        load_simple_list(
            session, os.path.join(base, "type.csv"), ItemType, ["type", "name", "kind"]
        )
        load_simple_list(
            session,
            os.path.join(base, "category.csv"),
            Category,
            ["category", "name", "class", "scale category"],
        )
        load_simple_list(
            session,
            os.path.join(base, "vendor.csv"),
            Vendor,
            ["vendor", "name", "store", "retailer", "marketplace"],
        )
        load_simple_list(
            session,
            os.path.join(base, "teams.csv"),
            Team,
            ["team", "teams", "name", "team_name"],
        )

        # Companies
        comp_path = os.path.join(base, "company.csv")
        if os.path.exists(comp_path):
            with open(comp_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    f.seek(0)
                    for line in f:
                        nm = line.strip().strip(",")
                        if nm:
                            get_or_create_by_name(session, Company, nm)
                else:
                    name_col = first_present(
                        reader.fieldnames, ["name", "company", "company_name", "brand"]
                    )
                    for row in reader:
                        nm = row.get(name_col, "").strip() if name_col else ""
                        if nm:
                            get_or_create_by_name(session, Company, nm)

        # Lines (with optional company link)
        line_path = os.path.join(base, "line.csv")
        if os.path.exists(line_path):
            with open(line_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    f.seek(0)
                    for line in f:
                        ln = line.strip().strip(",")
                        if ln:
                            get_or_create_by_name(session, Line, ln)
                else:
                    line_col = first_present(
                        reader.fieldnames,
                        [
                            "line",
                            "name",
                            "line_name",
                            "series (product line)",
                            "sub-line",
                            "subline",
                            "brand line",
                        ],
                    )
                    comp_col = first_present(
                        reader.fieldnames,
                        ["company", "company_name", "brand", "manufacturer"],
                    )
                    for row in reader:
                        ln = row.get(line_col, "").strip() if line_col else ""
                        if not ln:
                            continue
                        line = get_or_create_by_name(session, Line, ln)
                        if comp_col:
                            cn = row.get(comp_col, "").strip()
                            if cn:
                                comp = get_or_create_by_name(session, Company, cn)
                                if line and comp and line.company_id is None:
                                    line.company_id = comp.id
                                    session.add(line)
                                    session.commit()

        # Characters (with optional faction)
        char_path = os.path.join(base, "characters.csv")
        if os.path.exists(char_path):
            with open(char_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    f.seek(0)
                    for line in f:
                        nm = line.strip().strip(",")
                        if nm:
                            get_or_create_by_name(session, Character, nm)
                else:
                    name_col = first_present(
                        reader.fieldnames, ["character", "name", "character_name"]
                    )
                    faction_col = first_present(
                        reader.fieldnames, ["faction", "allegiance"]
                    )
                    for row in reader:
                        nm = row.get(name_col, "").strip() if name_col else ""
                        if not nm:
                            continue
                        char = session.exec(
                            select(Character).where(Character.name == nm)
                        ).first()
                        if not char:
                            char = Character(name=nm)
                        if faction_col:
                            fac = row.get(faction_col, "").strip()
                            if fac:
                                fac_obj = get_or_create_by_name(session, Faction, fac)
                                if fac_obj:
                                    char.faction_id = fac_obj.id
                        session.add(char)
                        session.commit()

    print("Seed from CSVs complete.")


if __name__ == "__main__":
    main()
