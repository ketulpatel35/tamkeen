from datetime import datetime
from odoo.report import report_sxw
from odoo import models, api
from odoo.api import Environment
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(
            cr, uid, name, context=context)
        self._cr, self._uid, self._context = cr, uid, context
        row = {}
        row['employee_basic'] = 0
        row['other_allowance'] = 0
        row['Deduction'] = 0

        self.localcontext.update({
            'get_employees_payslips': self.get_employees_payslips,
            'get_month': self.get_month,
            'get_nets': self.get_nets,
        })

    @api.model
    def get_employees_payslips(self, runs):
        row = {}
        rows = []
        self.env = Environment(self._cr, self._uid, self._context)

        for run in runs:
            for slip in run.slip_ids:  # looping through all employees
                # and get the info for each employee
                row['employee_name'] = slip.employee_id.name  # getting
                row[
                    'employee_bank_account'] = \
                    slip.employee_id.bank_account_id if \
                    slip.employee_id.bank_account_id else 0  # getting
                row[
                    'employee_bank_code'] = \
                    slip.employee_id.bank_account_id.acc_number if \
                    slip.employee_id.bank_account_id.acc_number else 0
                # getting employee bank code
                row['employee_net'] = 0.0
                row['employee_basic'] = 0.0
                row['H_Allowance'] = 0.0
                row['other_allowance'] = 0.0
                row['Deduction'] = 0.0
                row['employee_identification'] = 0
                for line in slip.line_ids:  # looping through lines
                    if line.code == "NET":  # checking if the type of the
                                            # amount is Net
                        row['employee_net'] = line.amount  # get the amount
                        # sum_nets +=	line.amount
                    elif line.code == "BNET":  # checking if the type of the
                                                # amount is Net
                        row['employee_basic'] = line.amount  # get the amount
                    elif line.code == 'HANET':
                        row['H_Allowance'] = line.amount
                    elif line.code == "TANET":
                        row['other_allowance'] = line.amount
                    elif line.code in ("BDED", "HADED", "TADED"):
                        row['Deduction'] += line.amount
                    elif line.code == "ALT":
                        row['other_allowance'] = line.amount
                    # checking if the employee is Saudi
                    if slip.employee_id.country_id.name == 'Saudi Arabia':
                        # get the identification id
                        row[
                            'employee_identification'] = \
                            slip.employee_id.identification_id
                    else:
                        # if non-Saudi employee get iqama number
                        row[
                            'employee_identification'] = \
                            slip.employee_id.identification_id

                rows.append(row)

                row = {}
        return rows

    @api.model
    def get_month(self, runs):
        monthsSymbolDict = {1: "JAN.", 2: "FEB.", 3: "MAR.", 4: "APR.",
                            5: "MAY.",
                            6: "JUN.", 7: "JUL.", 8: "AUG.", 9: "SEP.",
                            10: "OCT.",
                            11: "NOV.", 12: "DEC."}
        self.env = Environment(self._cr, self._uid, self._context)

        for run in runs:
            for slip in run.slip_ids:  # looping through all employees and
                                            # get the info for each employee
                date_start = slip.payslip_run_id.date_start  # getting the
                # start_date of the period
                date_start = datetime.\
                    strptime(date_start, OE_DATEFORMAT)  # format the date
                month_of_payslip_int = date_start.month  # return the month
                # number
                month_of_payslip = monthsSymbolDict[
                    month_of_payslip_int]  # return the month name
            return month_of_payslip

    @api.model
    def get_nets(self, runs):
        row = {}
        sum_nets = 0
        self.env = Environment(self._cr, self._uid, self._context)

        for run in runs:
            for slip in run.slip_ids:  # looping through all employees
                                        # and get the info for each employee
                for line in slip.line_ids:  # looping through lines
                    if line.code == "NET":  # checking if the type of the
                                            # amount is Net
                        row['employee_net'] = line.amount  # get the amount
                        sum_nets += line.amount
        return sum_nets


class qweb_payslip_run(models.AbstractModel):
    _name = 'report.hr_payroll_period.report_hr_payroll_bank_transfer'
    _inherit = 'report.abstract_report'
    _template = 'hr_payroll_period.report_hr_payroll_bank_transfer'
    _wrapped_report_class = Parser
