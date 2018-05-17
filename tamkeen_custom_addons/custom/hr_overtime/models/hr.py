from odoo import fields, models


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    cost_center_id = fields.Many2one('bs.costcentre')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string="Analytic Account")
    overtime_manager_id = fields.Many2one('hr.employee',
                                          string='Manager (Overtime Approval)',
                                          help='The responsible person for '
                                               'approving this employee '
                                               'Overtime/change requests as ')
    overtime_vp_id = fields.Many2one('hr.employee',
                                     string='VP (Overtime Approval)',
                                     help='The responsible person for '
                                          'approving this employee '
                                          'Overtime/change requests as a VP. ')
    overtime_ceo_id = fields.Many2one('hr.employee',
                                      string='CEO (Overtime Approval)',
                                      help='The responsible person for '
                                           'approving this employee '
                                           'Overtime/change requests as a '
                                           'CEO.')


class HRContract(models.Model):
    _inherit = 'hr.contract'

    hourly_rate = fields.Float(string='Hourly Rate', default=100)
