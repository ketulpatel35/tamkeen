# -*- coding: utf-8 -*-
from odoo import fields, models, api
import base64
import datetime
from odoo.exceptions import Warning
from random import randint
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re


class bank_ir8a_wizard(models.TransientModel):
    _name = "bank.ir8a.wizard"
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll'
                                                                    'Period')
    date_start = fields.Datetime(string='Period Start Date')
    date_end = fields.Datetime(string='Period End Date')
    payment_purpose_code = fields.Selection([('S', 'Salary'), ('B', 'Bonus'),
                                             ('O', 'Other Payments'),
                                             ('N', 'Non ACH Payments')],
                                            string='Payment Purpose Code',
                                            default='S',
                                            help="This field will identify the"
                                                 " purpose of the batch file."
                                                 "This can either be B - Bonus"
                                                 " payments /  O - Other "
                                                 "Payments / S - Salary / N - "
                                                 "Non ACH Payments . It should"
                                                 " be popluated with  a single"
                                                 " Characters as S / B / O "
                                                 "/ N.")
    payment_narration = fields.Char(string='Payment Narration',
                                    default='Salary',
                                    help="A "
                                         "Free text field of 35 characters is"
                                         " available to capture in payment "
                                         "details. Without special "
                                         "characters.")
    value_date = fields.Date(string='Value Date', help="Value date "
                                                       "of the payments in "
                                                       "YYYYMMDD format. Value"
                                                       " date should not be "
                                                       "less then the file "
                                                       "creation date and not "
                                                       "less than the current"
                                                       " date.")
    company_id = fields.Many2one('res.company', string='Company Name',
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get()
                                 )
    debit_account_number = fields.Char(string='Debit Account Number',
                                       help='Debit account number held with '
                                            'SABB. Debit account number needs'
                                            ' be populated without hyphens')
    mol_establishment_id = fields.Char(string='MOL Establishment ID',
                                       help='A unique ID provided by Minister'
                                            ' of Labour needs to be caputred '
                                            'here,it’s a numeric field it '
                                            'should be in the format of 2!d - '
                                            '15!d (99-999999999999999)')
    employer_id = fields.Char(string='Employer ID', help='A Customer or '
                                                         'Establishment '
                                                         'Registration '
                                                         'number.')
    connect_id = fields.Char(string='Connect ID',
                             help='Connect ID.')
    filename = fields.Char(string='File Name')
    data = fields.Binary(string='Export to File', readonly=True)
    report_destination = fields.Selection(
        [('bank', 'Bank'), ('other', 'Other')],
        string='Destination',
        help="The destination of the report, it may be for the bank or for "
             "any other purpose but in this case it will be displayed in more "
             "details.")

    @api.onchange('payroll_period_id')
    def onchange_payroll_period_id(self):
        if self.payroll_period_id:
            self.date_start = self.payroll_period_id.date_start
            self.date_end = self.payroll_period_id.date_end

    @api.onchange('company_id')
    def onchange_company_id(self):
        debit_account_number = ''
        if self.company_id and\
                self.company_id.payroll_partner_bank and\
                self.company_id.payroll_partner_bank.acc_number:
            debit_account_number =\
                self.company_id.payroll_partner_bank.acc_number
            self.employer_id = self.company_id.company_registry
            self.mol_establishment_id = self.company_id.mol_establishment_id
            self.connect_id = self.company_id.connect_id
        self.debit_account_number = debit_account_number

    @api.one
    def _compute_salary_rules(self, report_destination, payslip_line_ids):
        beneficiary_basic_salary = housing_allowance = other_earnings = \
            deductions = net_salary = 0
        salary_rules = {}
        for line in payslip_line_ids:
            if report_destination == "bank":
                if line.code == 'NET':
                    net_salary = line.total
            else:
                if line.code == 'BASIC':
                    beneficiary_basic_salary = line.total
                if line.code == 'HA':
                    housing_allowance = line.total
                if (line.category_id.code == 'ALW' or line.code == 'OE')\
                        and line.code != 'HA':
                    other_earnings += line.total
                # if line.code == 'OE':
                #         other_earnings += line.total
                if line.category_id.code == 'DED':  # OD
                    deductions += line.total

                if line.code == 'NET':
                    net_salary = line.total
        if deductions:
            deductions = deductions * -1
        salary_rules.update({
            'beneficiary_basic_salary': beneficiary_basic_salary,  #
            'housing_allowance': housing_allowance,
            'other_earnings': other_earnings,
            'deductions': deductions,
            'net_salary': net_salary,
        })
        return salary_rules

    @api.multi
    def action_generate_bank_ir8a(self):

        for rec in self:
            current_datetime = datetime.datetime.now().strftime(DF)
            last_name = ''
            if rec.value_date < current_datetime:
                raise Warning(
                    "Value date should not be less then the "
                    "file creation date.")

            creation_date = datetime.datetime.now().strftime(
                "%Y%m%d")  # ("%Y/%m/%d")
            value_date = datetime.datetime.strptime(rec.value_date, DF)
            value_date = value_date.strftime('%Y%m%d')
            # employee_id #Beneficiary's Employee ID.
            # This has to be unique within a file.
            # bank id #Bank ID/ SWIFT ID to identify the bank.
            # Payment Amount #Payment amount to the employee. With two decimal
            # places No preceeding zeros allowed
            file_reference = str(datetime.datetime.now().strftime(
                "%d%H%M%S%f")[:-1]) + str(randint(111, 999))
            file_name = 'WPS.9883.CY.SAR.' + file_reference + ".txt"
            # .now().strftime("%Y%m%d%H%M%S"))
            # batch_reference = 'W' + str(datetime.datetime.now().
            # strftime("%Y%m%d%H%M%S"))

            record_number, total_sum = 0, 0.0
            employee_line, line2 = "", ""
            payslip_obj = self.env['hr.payslip']

            period_payslip_ids = payslip_obj.search([('date_from', '>=',
                                                      rec.date_start),
                                                     ('date_to', '<=',
                                                      rec.date_end)])

            for payslip in period_payslip_ids:
                if payslip.employee_id.country_id and \
                        payslip.employee_id.country_id.code == "SA":
                    employee_identity = payslip.employee_id.identification_id
                else:
                    employee_identity = payslip.employee_id.iqama_number
                if employee_identity and payslip.employee_id.bank_account and \
                        payslip.employee_id.bank_id.bic:
                    record_number += 1
                    salary_rules = self._compute_salary_rules(
                        rec.report_destination, payslip.line_ids)
                    for salary in salary_rules:
                        total_sum += salary['net_salary']

                        formatted_beneficiary_basic_salary = (
                            '%.2f' % salary[
                                'beneficiary_basic_salary']).replace(
                            '.', ',')
                        formatted_housing_allowance = (
                            '%.2f' % salary['housing_allowance']).replace(
                            '.',
                            ',')
                        formatted_other_earnings = (
                            '%.2f' % salary['other_earnings'])\
                            .replace('.', ',')
                        formatted_deductions = (
                            '%.2f' % salary['deductions']).replace('.', ',')
                        formatted_net_salary = (
                            '%.2f' % salary['net_salary']).replace('.', ',')

                    # employee_line = \
                    #     "%s\t%s\t%s\t%s\t%s\t%s\t
                    # %s\t%s\t%s\t%s\t%s\t%s\t%s" \
                    #     "\t%s\r\n" % (formatted_net_salary,
                    #                   payslip.employee_id.bank_account,
                    #                   payslip.employee_id.name,
                    #                   payslip.employee_id.bank_id.bic,
                    #                   rec.payment_narration, space,
                    #                   formatted_beneficiary_basic_salary,
                    #                   formatted_housing_allowance,
                    #                   formatted_other_earnings,
                    #                   formatted_deductions,
                    #  employee_identity,
                    #                   space, space, space)

                    if payslip.employee_id and payslip.employee_id.name:
                        full_name_lst = re.findall(r"[\w']+",
                                                   payslip.employee_id.name)
                        first_name, second_name, last_name, payroll_name\
                            = '', '', '', ''
                        if full_name_lst:
                            first_name = full_name_lst[0]
                            if full_name_lst and len(full_name_lst) > 1:
                                second_name = full_name_lst[1]
                            if len(full_name_lst) > 2:
                                last_name = full_name_lst[-1]
                        payroll_name =\
                            first_name + ' ' +\
                            second_name + ' ' + last_name
                    employee_line = "%s\t%s\t%s\t%s\t%s\t\t" \
                                    "%s\t%s\t%s\t%s\t%s\t\t\t\r\n" %\
                                    (formatted_net_salary,
                                     payslip.employee_id.bank_account,
                                     payroll_name,
                                     payslip.employee_id.bank_id.bic,
                                     rec.payment_narration,
                                     formatted_beneficiary_basic_salary,
                                     formatted_housing_allowance,
                                     formatted_other_earnings,
                                     formatted_deductions,
                                     employee_identity)

                    line2 += employee_line
                    # else:
                    #     raise Warning("Please, Before proceeding with
                    # exporting this file, Make sure that the following data
                    # has been filled for this employee '"+ payslip.
                    # employee_id.name +"':\n\n - Identification No or Iqama
                    # Number.\n - Employee Bank Account Number.\n - Bank
                    # Identifier Code. \n")

            # in the file.
            total_sum = ('%.2f' % total_sum).replace('.',
                                                     ',')  # The total amount
            # being paid out through the payment file.

            # line1 = "AAAL\t%s\t%s\tSAR\t%s\t%s\t%s\t%s\t%s\t%s\r\n" % (
            #     rec.connect_id, rec.debit_account_number, creation_date,
            #     total_sum, value_date, file_reference, space,
            #     rec.mol_establishment_id)
            #
            # output = line1 + line2
            # rec.data = base64.encodestring(output.encode('utf-8'))

            line1 = "AAAL\t%s\t%s\tSAR\t%s\t%s\t%s\t%s\t\t%s\r\n" % (
                rec.connect_id, rec.debit_account_number,
                creation_date, total_sum, value_date,
                file_reference, rec.mol_establishment_id)
            line3 = "-"
            output = line1 + line2 + line3
            self.write({'data': base64.encodestring(
                output.encode('windows-1256')), 'filename': file_name})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bank.ir8a.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
