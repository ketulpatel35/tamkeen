from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    loan_manager_id = fields.Many2one('hr.employee',
                                          string='Manager (Loan Approval)',
                                          help='The responsible person for '
                                               'approving this employee '
                                               'Loan/change requests as ')
    loan_vp_id = fields.Many2one('hr.employee',
                                     string='VP (Loan Approval)',
                                     help='The responsible person for '
                                          'approving this employee '
                                          'Loan/change requests as a VP. ')
    loan_ceo_id = fields.Many2one('hr.employee',
                                      string='CEO (Loan Approval)',
                                      help='The responsible person for '
                                           'approving this employee '
                                           'Loan/change requests as a '
                                           'CEO.')
