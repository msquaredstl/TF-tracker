from datetime import date

from app.main import imported_items
from app.models import Company, Item, Purchase, Vendor


def test_imported_items_page_displays_imported_rows(session, request_factory) -> None:
    company = Company(name="Hasbro")
    vendor = Vendor(name="Amazon")
    session.add(company)
    session.add(vendor)
    session.commit()

    item = Item(name="Optimus Prime", status="Owned", company_id=company.id)
    session.add(item)
    session.commit()

    purchase = Purchase(
        item_id=item.id,
        vendor_id=vendor.id,
        price=29.99,
        currency="USD",
        purchase_date=date(2023, 5, 1),
    )
    session.add(purchase)
    session.commit()

    response = imported_items(request_factory("/imports"), session=session)
    assert response.status_code == 200

    content = response.template.render(response.context)
    assert "Optimus Prime" in content
    assert "Amazon" in content
    assert "2023-05-01" in content
    assert "USD 29.99" in content


def test_imported_items_page_handles_empty_state(session, request_factory) -> None:
    response = imported_items(request_factory("/imports"), session=session)
    assert response.status_code == 200
    assert "No imported data available yet." in response.template.render(response.context)
