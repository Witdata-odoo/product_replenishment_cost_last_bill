from odoo import Command
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestLastBill(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Last bill product", "replenishment_cost_type": "last_vendor_bill"}
        )
        cls.tmpl = cls.product.product_tmpl_id

    def _bill(self, price, date, discount=0.0, post=True):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": date,
                "invoice_line_ids": [
                    Command.create(
                        {"product_id": self.product.id, "quantity": 1, "price_unit": price, "discount": discount}
                    )
                ],
            }
        )
        if post:
            bill.action_post()
        self.env.invalidate_all()
        return bill

    def _cost(self, bill):
        return self.tmpl.with_company(bill.company_id).replenishment_cost

    def test_no_bill_is_zero(self):
        self.assertEqual(self.tmpl.replenishment_cost, 0.0)

    def test_last_bill_by_invoice_date(self):
        self._bill(100.0, "2026-01-10")
        bill = self._bill(50.0, "2026-01-05")  # older invoice date posted later
        self.assertEqual(self._cost(bill), 100.0)

    def test_discount_and_draft_ignored(self):
        self._bill(100.0, "2026-01-10", discount=10.0)
        bill = self._bill(500.0, "2026-02-10", post=False)
        self.assertEqual(self._cost(bill), 90.0)

    def test_other_type_unaffected(self):
        self.tmpl.replenishment_cost_type = "manual"
        self._bill(100.0, "2026-01-10")
        self.assertNotEqual(self.product.standard_price, 100.0)