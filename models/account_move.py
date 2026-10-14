from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted.filtered(lambda m: m.move_type == "in_invoice"):
            templates = move.invoice_line_ids.filtered(lambda l: l.display_type == "product").product_id.product_tmpl_id
            templates = templates.filtered(lambda t: t.replenishment_cost_type == "last_vendor_bill")
            if templates:
                templates.with_company(move.company_id)._update_cost_from_replenishment_cost()
        return posted
