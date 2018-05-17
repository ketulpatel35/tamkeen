from odoo import models, fields


class CleansingXLSReport(models.TransientModel):
    _name = 'cleansing.xls.report'

    xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Attendance_Report.xls')
