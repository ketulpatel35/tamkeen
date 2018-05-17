from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    expense_manager_id = fields.Many2one('hr.employee',
                                          string='Manager (Expense Approval)',
                                          help='The responsible person for '
                                               'approving this employee '
                                               'Expense requests as ')
    expense_vp_id = fields.Many2one('hr.employee',
                                     string='VP (Expense Approval)',
                                     help='The responsible person for '
                                          'approving this employee '
                                          'Expense requests as a VP. ')
    expense_ceo_id = fields.Many2one('hr.employee',
                                      string='CEO (Expense Approval)',
                                      help='The responsible person for '
                                           'approving this employee '
                                           'Expense requests as a '
                                           'CEO.')
