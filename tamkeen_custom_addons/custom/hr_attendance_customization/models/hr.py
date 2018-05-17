# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import fields, models


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    attendance_manager_id = fields.Many2one('hr.employee',
                                            string='Attendance Manager',
                                            help='The responsible person for '
                                                 'approving this employee '
                                                 'Attendance/Change Request '
                                                 'as a manager.')
    attendance_vp_id = fields.Many2one('hr.employee',
                                       string='VP (Attendance Approval)',
                                       help='The responsible person for '
                                            'approving this employee '
                                            'attendance/change '
                                            'requests as a VP.')
    attendance_ceo_id = fields.Many2one('hr.employee',
                                        string='CEO (Attendance Approval)',
                                        help='The responsible person for '
                                             'approving this employee '
                                             'attendance/change requests '
                                             'as a CEO.')
