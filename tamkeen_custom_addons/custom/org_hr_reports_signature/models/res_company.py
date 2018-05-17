from odoo import models, api, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'


    payslip_certificate_stamp = fields.Binary(string='PaySlip '
                                                 'Stamp')
    payslip_certificate_signature = fields.Binary(string='PaySlip '
                                                        'Signature')
    authorised_employee_id = fields.Many2one('hr.employee',
                                             string='Authorised Official')
    authorised_employee_email = fields.Char('PaySlip Reports Contact Email')