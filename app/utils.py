from typing import List, Optional, Type, TypeVar
from sqlmodel import SQLModel, Session, select

T = TypeVar("T", bound=SQLModel)


def split_characters(value: Optional[str]) -> List[str]:
    if not value:
        return []

    tokens = value.replace(";", "\n").replace(",", "\n").splitlines()
    entries: List[str] = []
    for raw in tokens:
        token = raw.strip()
        if not token:
            continue

        if "|" in token:
            parts = [part.strip() for part in token.split("|")]
            head = parts[0]
            tail = [part for part in parts[1:] if part]
            if tail:
                token = head + " |" + " |".join(tail)
            else:
                token = head

        entries.append(token)

    return entries


def get_or_create(session: Session, model: type[T], name: Optional[str]) -> Optional[T]:
    if not name:
        return None
    name = name.strip()
    if not name:
        return None
    stmt = select(model).where(model.name == name)
    obj = session.exec(stmt).first()
    if obj:
        return obj
    obj = model(name=name)  # type: ignore
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj
