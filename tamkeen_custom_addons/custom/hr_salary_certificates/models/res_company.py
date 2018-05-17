from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'


    salary_certificate_stamp = fields.Binary(string='Employment Certificate Stamp')
    salary_certificate_signature = fields.Binary(string='Employment Certificate '
                                                        'Signature')