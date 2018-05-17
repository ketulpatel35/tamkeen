# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
#
try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api
import datetime as DT
import base64
from datetime import datetime
from cStringIO import StringIO
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


# class HrPayrollPeriod(models.Model):
#     _inherit = 'hr.payroll.period.end.1'
#     _description = 'Payroll Sheet Excel Report'
#
#     @api.multi
#     def print_report(self):
#         return {
#             # "type": "ir.actions.act_url",
#             # "url": str(base_url) + str(download_url),
#             # "target": "self",
#             'context': self.env.context,
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'payroll.period.report.xls',
#             'type': 'ir.actions.act_window',
#             'target': 'new'
#         }
