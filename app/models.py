from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, JSON
from datetime import date

class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    lines: List["Line"] = Relationship(back_populates="company")
    items: List["Item"] = Relationship(back_populates="company")

class Line(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    company: Optional[Company] = Relationship(back_populates="lines")
    items: List["Item"] = Relationship(back_populates="line")

class Series(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    items: List["Item"] = Relationship(back_populates="series")

class ItemType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    items: List["Item"] = Relationship(back_populates="type")

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    items: List["Item"] = Relationship(back_populates="category")

class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    purchases: List["Purchase"] = Relationship(back_populates="vendor")

class Faction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    characters: List["Character"] = Relationship(back_populates="faction")

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    character_links: List["CharacterTeam"] = Relationship(back_populates="team")

class Character(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    faction_id: Optional[int] = Field(default=None, foreign_key="faction.id")
    faction: Optional[Faction] = Relationship(back_populates="characters")
    aliases: Optional[str] = None

    team_links: List["CharacterTeam"] = Relationship(back_populates="character")
    item_links: List["ItemCharacter"] = Relationship(back_populates="character")

class CharacterTeam(SQLModel, table=True):
    character_id: int = Field(foreign_key="character.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    character: Character = Relationship(back_populates="team_links")
    team: Team = Relationship(back_populates="character_links")

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    item_links: List["ItemTag"] = Relationship(back_populates="tag")

class ItemTag(SQLModel, table=True):
    item_id: int = Field(foreign_key="item.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
    tag: Tag = Relationship(back_populates="item_links")
    item: "Item" = Relationship(back_populates="tag_links")

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: Optional[str] = Field(default=None, index=True)
    version: Optional[str] = None
    year: Optional[int] = Field(default=None, index=True)
    scale: Optional[str] = Field(default=None, index=True)
    condition: Optional[str] = Field(default=None, index=True)
    status: Optional[str] = Field(default="Owned", index=True)
    location: Optional[str] = Field(default=None, index=True)
    url: Optional[str] = None
    notes: Optional[str] = None
    extra: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)

    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    line_id: Optional[int] = Field(default=None, foreign_key="line.id")
    series_id: Optional[int] = Field(default=None, foreign_key="series.id")
    type_id: Optional[int] = Field(default=None, foreign_key="itemtype.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")

    company: Optional[Company] = Relationship(back_populates="items")
    line: Optional[Line] = Relationship(back_populates="items")
    series: Optional[Series] = Relationship(back_populates="items")
    type: Optional[ItemType] = Relationship(back_populates="items")
    category: Optional[Category] = Relationship(back_populates="items")

    character_links: List["ItemCharacter"] = Relationship(back_populates="item")
    purchases: List["Purchase"] = Relationship(back_populates="item")
    tag_links: List[ItemTag] = Relationship(back_populates="item")

class ItemCharacter(SQLModel, table=True):
    item_id: int = Field(foreign_key="item.id", primary_key=True)
    character_id: int = Field(foreign_key="character.id", primary_key=True)
    is_primary: bool = Field(default=False)
    role: Optional[str] = None
    item: Item = Relationship(back_populates="character_links")
    character: Character = Relationship(back_populates="item_links")

class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    vendor_id: Optional[int] = Field(default=None, foreign_key="vendor.id")
    purchase_date: Optional[date] = None
    price: Optional[float] = None
    tax: Optional[float] = None
    shipping: Optional[float] = None
    currency: Optional[str] = None
    order_number: Optional[str] = None
    notes: Optional[str] = None

    item: Item = Relationship(back_populates="purchases")
    vendor: Optional[Vendor] = Relationship(back_populates="purchases")
