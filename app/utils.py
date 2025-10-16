from typing import Optional, Type, TypeVar
from sqlmodel import SQLModel, Session, select

T = TypeVar("T", bound=SQLModel)

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
