from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    pa_manager_id = fields.Many2one(
        'hr.employee', string='Manager (Appraisal Performance)',
        help='The responsible person for approving this employee Business '
             'Trip requests.')
    pa_vp_id = fields.Many2one(
        'hr.employee', string='VP (Appraisal Performance)',
        help='The responsible person for approving this employee Appraisal '
             'Performance requests as a VP.')
    pa_ceo_id = fields.Many2one(
        'hr.employee', string='CEO (Appraisal Performance)',
        help='The responsible person for approving this employee Appraisal '
             'Performance requests as a CEO.')
