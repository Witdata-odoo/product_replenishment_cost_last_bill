{
    "name": "Replenishment Cost from Last Vendor Bill",
    "version": "18.0.1.0.0",
    "author": "WITDATA",
    "license": "AGPL-3",
    "category": "Products",
    "summary": "Update replenishment cost based on the last posted vendor bill",
    "depends": [
        "product_replenishment_cost",
        "account",
    ],
    "data": [
        "views/product_template_views.xml",
    ],
    "installable": True,
}
