from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    payroll_journal_id = fields.\
        Many2one('account.journal',
                 string='Default Payroll Journal')
    payroll_lock_day = fields.Integer(string='Scheduled Payroll Lock Day')
