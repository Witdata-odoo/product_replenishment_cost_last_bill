from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    replenishment_cost_type = fields.Selection(
        selection_add=[("last_vendor_bill", "Last Vendor Bill")],
        ondelete={"last_vendor_bill": "set default"},
    )

    @api.depends_context("company")
    @api.depends("replenishment_cost_type")
    def _compute_supplier_data(self):
        super()._compute_supplier_data()
        bill_products = self.filtered(lambda p: p.replenishment_cost_type == "last_vendor_bill")
        for rec in bill_products:
            price, currency = rec._get_last_vendor_bill_price()
            rec.update({"supplier_price": price, "supplier_currency_id": currency})

    def _get_last_vendor_bill_price(self):
        """Return (price, currency) from the last posted vendor bill line (by invoice date).
        Price is untaxed, with line discount, expressed in the purchase UoM of the product."""
        self.ensure_one()
        line = (
            self.env["account.move.line"]
            .sudo()
            .search(
                [
                    ("move_id.move_type", "=", "in_invoice"),
                    ("move_id.state", "=", "posted"),
                    ("display_type", "=", "product"),
                    ("product_id.product_tmpl_id", "=", self.id),
                    ("company_id", "=", self.env.company.id),
                    ("invoice_date", "!=", False),
                ],
                order="invoice_date desc, id desc",
                limit=1,
            )
        )
        if not line:
            return 0.0, self.env["res.currency"]
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        if line.product_uom_id and self.uom_po_id and line.product_uom_id != self.uom_po_id:
            price = line.product_uom_id._compute_price(price, self.uom_po_id)
        return price, line.currency_id
