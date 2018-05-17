from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'


    minimum_allowed_unpaid_days = fields.Float(string='Minimum Allowed Unpaid'
                                                 'Days(Lock)', help='The '
                                                                    'Minimum allowed unpaid days for locking the employee benefits.')