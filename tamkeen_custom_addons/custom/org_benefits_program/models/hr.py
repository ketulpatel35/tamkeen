from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _count_children_age_5_18(self):
        """
        count number of children eligible for education benefits
        :return:
        """
        for rec in self:
            rec.children_age_5_18 = \
                self.env['employee.family.info'].search_count([
                    ('employee_id', '=', rec.id),
                    ('relationship', 'in', ['son', 'daughter']),
                    ('age','>=', 5),
                    ('age', '<=', 18)])

    bp_manager_id = fields.Many2one(
        'hr.employee', string='Manager (Benefits Program)',
        help='The responsible person for approving this employee Benefits '
             'Program requests.')
    bp_vp_id = fields.Many2one(
        'hr.employee', string='VP (Benefits Program)',
        help='The responsible person for approving this employee Benefits '
             'Program requests as a VP.')
    bp_ceo_id = fields.Many2one(
        'hr.employee', string='CEO (Benefits Program)',
        help='The responsible person for approving this employee Benefits '
             'Program requests as a CEO.')
    children_age_5_18 = fields.Integer('Children Age 5-18',
                                       compute='_count_children_age_5_18')