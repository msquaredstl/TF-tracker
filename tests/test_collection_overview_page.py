from datetime import date

from app.main import collection_overview
from app.models import Company, Item, Purchase, Vendor


def test_collection_overview_displays_summary_and_items(
    session, request_factory
) -> None:
    company = Company(name="Hasbro")
    session.add(company)
    session.commit()

    vendor = Vendor(name="Pulse")
    session.add(vendor)
    session.commit()

    item = Item(name="Bumblebee", status="Owned", company_id=company.id)
    item.extra = {"owner_id": "alpha"}
    session.add(item)
    session.commit()

    purchase = Purchase(
        item_id=item.id,
        vendor_id=vendor.id,
        price=59.99,
        currency="USD",
        purchase_date=date(2022, 3, 15),
    )
    session.add(purchase)
    session.commit()

    response = collection_overview(request_factory("/collection"), session=session)
    assert response.status_code == 200

    content = response.template.render(response.context)
    assert "Total items" in content
    assert "Bumblebee" in content
    assert "USD 59.99" in content
    assert "Hasbro" in content
    assert "Owned" in content
    assert "Companies represented" in content


def test_collection_overview_filters_by_owner_identifier(
    session, request_factory
) -> None:
    company = Company(name="Takara")
    session.add(company)
    session.commit()

    alpha_item = Item(name="Optimus", status="Owned", company_id=company.id)
    alpha_item.extra = {"owner_id": "alpha"}
    beta_item = Item(name="Megatron", status="Wishlist", company_id=company.id)
    beta_item.extra = {"owner_id": "beta"}
    session.add(alpha_item)
    session.add(beta_item)
    session.commit()

    response = collection_overview(
        request_factory("/collection", {"owner": "alpha"}),
        owner="alpha",
        session=session,
    )
    assert response.status_code == 200

    content = response.template.render(response.context)
    assert "Optimus" in content
    assert "Megatron" not in content
    assert "owner <strong>alpha" in content
