from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    timesheet_manager_id = fields.Many2one('hr.employee',
                                          string='Manager (Timesheet '
                                                 'Approval)',
                                          help='The responsible person for '
                                               'approving this employee '
                                               'timesheet/change requests as ')
    timesheet_vp_id = fields.Many2one('hr.employee',
                                     string='VP (Timesheet Approval)',
                                     help='The responsible person for '
                                          'approving this employee '
                                          'timesheet/change requests as a VP. ')
    timesheet_ceo_id = fields.Many2one('hr.employee',
                                      string='CEO (Timesheet Approval)',
                                      help='The responsible person for '
                                           'approving this employee '
                                           'timesheet/change requests as a '
                                           'CEO.')
