from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    eos_manager_id = fields.Many2one(
        'hr.employee', string='Manager (End of Service)',
        help='The responsible person for approving this employee End of '
             'Service requests.')
    eos_vp_id = fields.Many2one(
        'hr.employee', string='VP (End of Service)',
        help='The responsible person for approving this employee End of '
             'Service requests as a VP.')
    eos_ceo_id = fields.Many2one(
        'hr.employee', string='CEO (End of Service)',
        help='The responsible person for approving this employee End of '
             'Service requests as a CEO.')
