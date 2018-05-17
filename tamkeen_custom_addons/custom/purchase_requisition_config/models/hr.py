from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    pr_manager_id = fields.Many2one('hr.employee',
                                    string='Manager (Purchase Requisition '
                                           'Approval)',
                                    help='The responsible person for '
                                         'approving this employee Purchase '
                                         'Requisition/change requests as ')
    pr_vp_id = fields.Many2one('hr.employee',
                               string='VP (Purchase Requisition Approval)',
                               help='The responsible person for approving '
                                    'this employee Purchase '
                                    'Requisition/change requests as a VP.')
    pr_ceo_id = fields.Many2one('hr.employee',
                                string='CEO (Purchase Requisition Approval)',
                                help='The responsible person for approving '
                                     'this employee Purchase '
                                     'Requisition/change requests as a CEO.')
