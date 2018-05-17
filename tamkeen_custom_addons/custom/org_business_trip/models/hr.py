from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bt_manager_id = fields.Many2one(
        'hr.employee', string='Manager (Business Trip)',
        help='The responsible person for approving this employee Business '
             'Trip requests.')
    bt_vp_id = fields.Many2one(
        'hr.employee', string='VP (Business Trip)',
        help='The responsible person for approving this employee Business '
             'Trip requests as a VP.')
    bt_ceo_id = fields.Many2one(
        'hr.employee', string='CEO (Business Trip)',
        help='The responsible person for approving this employee Business '
             'Trip requests as a CEO.')
