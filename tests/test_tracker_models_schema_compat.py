from tracker import models, schema


def test_configure_schema_keeps_purchase_date_columns(monkeypatch):
    purchase_table = models.Purchase._meta.db_table

    def fake_table_has_column(table, column):
        if table == purchase_table and column in {"order_date", "ship_date"}:
            return False
        return True

    monkeypatch.setattr(schema, "table_has_column", fake_table_has_column, raising=False)
    models.configure_schema_compatibility(force=True)

    order_field = models.Purchase._meta.get_field("order_date")
    ship_field = models.Purchase._meta.get_field("ship_date")

    assert order_field.column == "order_date"
    assert ship_field.column == "ship_date"

    monkeypatch.undo()
    models.configure_schema_compatibility(force=True)


def test_configure_schema_uses_rowid_for_join_tables(monkeypatch):
    join_tables = {
        models.CharacterTeam._meta.db_table,
        models.ItemCharacter._meta.db_table,
        models.ItemTag._meta.db_table,
    }

    def fake_table_has_column(table, column):
        if column == "id" and table in join_tables:
            return False
        return True

    monkeypatch.setattr(schema, "table_has_column", fake_table_has_column, raising=False)
    models.configure_schema_compatibility(force=True)

    for model in (models.CharacterTeam, models.ItemCharacter, models.ItemTag):
        assert model._meta.pk.column == "rowid"

    monkeypatch.undo()
    models.configure_schema_compatibility(force=True)


def test_configure_schema_falls_back_for_quantity(monkeypatch):
    purchase_table = models.Purchase._meta.db_table

    def fake_table_has_column(table, column):
        if table == purchase_table and column == "qty":
            return False
        return True

    monkeypatch.setattr(schema, "table_has_column", fake_table_has_column, raising=False)
    models.configure_schema_compatibility(force=True)

    quantity_field = models.Purchase._meta.get_field("quantity")
    assert quantity_field.column == "quantity"

    monkeypatch.undo()
    models.configure_schema_compatibility(force=True)
