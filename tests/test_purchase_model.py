from datetime import date
from unittest import TestCase

from app.models import Purchase


class PurchaseModelTests(TestCase):
    def test_order_and_ship_dates_are_optional(self) -> None:
        purchase = Purchase(order_date=date(2023, 1, 5), ship_date=date(2023, 2, 1))

        self.assertEqual(purchase.order_date, date(2023, 1, 5))
        self.assertEqual(purchase.ship_date, date(2023, 2, 1))

    def test_purchase_defaults_to_missing_dates(self) -> None:
        purchase = Purchase()

        self.assertIsNone(purchase.order_date)
        self.assertIsNone(purchase.ship_date)
