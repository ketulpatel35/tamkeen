from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_supplier_advance = fields\
        .Many2one('account.account',
                  string="Account Supplier Advance",
                  help="This account will be"
                       " used for advance payment of suppliers")

    property_account_customer_advance = fields\
        .Many2one('account.account',
                  string="Account Customer Advance",
                  help="This account will be"
                       " used for advance payment of custom")
