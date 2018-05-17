# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, models, fields


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    destination_english = fields.Char(string='Destination English')
    destination_arabic = fields.Char(string='Destination Arabic')

    @api.model
    def get_line_total(self, var):
        total = 0
        for line in self.line_ids:
            if line.name == var:
                total += line.total
        return total


class HrPayslipWizard(models.Model):

    _name='hr.payslip.wizard'

    destination_english = fields.Char(string='Destination in English')
    destination_arabic = fields.Char(string='Destination in Arabic')
    report_selection = fields.Selection([('salary_certification', 'Salary '
                                                        'Certification'),
                                ('salary_certi_embassy', 'Salary '
                                                         'Certification Embassy'),
                                ('salary_certi_gross', 'Salary Certification '
                                                  'Gross'),
                                ('salary_certi_no', 'Salary Certification '
                                                    'No')],
                               string='Certification',
                                        default='salary_certification')

    def generate_report(self, context=None):
        if context is None:
            context = {}
        if context.get('active_id'):
            pay_obj = self.env['hr.payslip'].browse(context.get('active_id'))
            pay_obj.destination_english= self.destination_english
            pay_obj.destination_arabic = self.destination_arabic
        if self.report_selection == 'salary_certification':
            return self.env['report'].get_action(context.get('active_id'),
                                                 'salary_certificate_report.salary_certificate_detail_report_template_id')
        elif self.report_selection == 'salary_certi_embassy':
            return self.env['report'].get_action(context.get('active_id'),
                                                     'salary_certificate_report.salary_certificate_embassy_report_template_id')
        elif self.report_selection == 'salary_certi_gross':
            return self.env['report'].get_action(context.get('active_id'),
                                             'salary_certificate_report.salary_certificate_gross_report_template_id')
        elif self.report_selection == 'salary_certi_no':
            return self.env['report'].get_action(context.get('active_id'),
                                                 'salary_certificate_report.salary_certificate_no_report_template_id')