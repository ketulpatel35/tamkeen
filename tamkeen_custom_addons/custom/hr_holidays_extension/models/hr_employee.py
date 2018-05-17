from odoo import models, fields


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    current_leave_state = fields.\
        Selection(compute='_compute_leave_status',
                  string="Current Leave Status",
                  selection=[('draft', 'To Submit'),
                             ('confirm', 'Manager Approval'),
                             ('vp', 'VP Approval'),
                             ('validate1', 'HR Approval'),
                             ('ceo', 'CEO Approval'),
                             ('validate', 'Approved'),
                             ('cancel', 'Cancelled'),
                             ('refuse', 'Refused'),
                             ('leave_approved', 'Validate')])
    leave_manager_id = fields.Many2one('hr.employee',
                                      string='Manager (Leave Approval)',
                                      help='The responsible person for '
                                           'approving this employee '
                                           'Loan/change requests as ')
    leave_vp_id = fields.Many2one('hr.employee',
                                 string='VP (Leave Approval)',
                                 help='The responsible person for '
                                      'approving this employee '
                                      'Loan/change requests as a VP. ')
    leave_ceo_id = fields.Many2one('hr.employee',
                                  string='CEO (Leave Approval)',
                                  help='The responsible person for '
                                       'approving this employee '
                                       'Loan/change requests as a '
                                       'CEO.')