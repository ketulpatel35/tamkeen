try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields, _
import time
from cStringIO import StringIO
import base64
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime



class EmployeeSalarySummary(models.Model):
    _name = 'hr.employee.salary.summary'
    _description = 'Employee Salary Summary'

    DEPT = []
    vals = {'section': False, 'department': False,
            'business': False}

    @api.model
    def set_header(self, worksheet):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """
        worksheet.row(0).height = 600
        for for_col in range(0, 16):
            worksheet.col(for_col).width = 256 * 19
        s2 = xlwt.easyxf(
            'font: bold 1,height 180 ,colour h2_text_color;'
            'alignment: horizontal center, wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        worksheet.write(0, 0, 'Employee ID', s2)
        worksheet.write(0, 1, 'Employee Name', s2)
        worksheet.write(0, 2,'Business Unit', s2)
        worksheet.write(0, 3, 'Department', s2)
        worksheet.write(0, 4, 'Section', s2)
        worksheet.write(0, 5, 'Cost Center', s2)
        worksheet.write(0, 6, 'Date of Joining', s2)
        worksheet.write(0, 7, 'Nationality', s2)
        worksheet.write(0, 8, 'Career Band / or Job', s2)
        worksheet.write(0, 9, 'Grade', s2)
        worksheet.write(0, 10, 'Job Title', s2)
        worksheet.write(0, 11, 'Current Base Salary', s2)
        worksheet.write(0, 12, 'Housing Allowance', s2)
        worksheet.write(0, 13, 'Transportation', s2)
        worksheet.write(0, 14, 'Other Earnings', s2)
        worksheet.write(0, 15, 'Total', s2)

    def _get_department(self, dept_rec):
        """
        :return:
        """
        if dept_rec.org_unit_type == 'department':
            return dept_rec
        if dept_rec.org_unit_type == 'business':
            return False
        if dept_rec.parent_id:
            return self._get_department(dept_rec.parent_id)
        return False

    def _get_business_unit(self, dept_rec):
        """
        :return:
        """
        if dept_rec.org_unit_type == 'business':
            return dept_rec
        if dept_rec.parent_id:
            return self._get_business_unit(dept_rec.parent_id)
        return False

    @api.multi
    def salary_data(self , emp):
        rule_value_dict = {}
        data = self.get_latest_contract_structure_localdict(emp)
        lst = ['HA', 'TA', 'BASIC']
        if data:
            for line in lst:
                if line in data:
                    rule_value_dict.update({
                        line: data[line] or 0.00,
                    })
            total = sum(rule_value_dict.values())
        rule_value_dict.update({'total': total})
        for key, value in rule_value_dict.items():
            rule_value_dict.update({key: '{:0.2f}'.format(abs(value))})
        return rule_value_dict

    @api.multi
    def get_allowences_data(self, emp):
        rule_value_dict = {}
        data = self.get_latest_contract_structure_localdict(emp)
        if data and data.get('all_allowances'):
            rule_value_dict.update({'total': data.get('all_allowances')})
        for key, value in rule_value_dict.items():
            rule_value_dict.update({key: '{:0.2f}'.format(abs(value))})
        return rule_value_dict

    @api.multi
    def get_latest_contract_structure_localdict(self , emp):
        blacklist = []
        for rec in self:
            def _sum_salary_rule_category(localdict, category, amount):
                if category.parent_id:
                    localdict = _sum_salary_rule_category(localdict,
                                                          category.parent_id,
                                                          amount)
                localdict[
                    'categories'].dict[category.code] = \
                    category.code in localdict['categories'].dict and \
                    localdict['categories'].dict[category.code] + amount or amount
                return localdict

            class BrowsableObject(object):

                def __init__(self, employee_id, dict, env):
                    self.employee_id = employee_id
                    self.dict = dict
                    self.env = env

                def __getattr__(self, attr):
                    return attr in self.dict and self.dict.__getitem__(attr) or 0.0

            rules_dict = {}
            current_rule_ids = []
            sorted_rules_new = []
            if emp.contract_id and emp.contract_id.struct_id:
                contract_struct_rec = emp.contract_id.struct_id \
                    ._get_parent_structure()
                for struct in contract_struct_rec:
                    sort_current_rule_ids = struct.rule_ids.ids
                    current_rule_ids += list(set(sort_current_rule_ids))
            categories = BrowsableObject(emp.id, {}, self.env)
            rules = BrowsableObject(emp.id, rules_dict, self.env)
            baselocaldict = {'categories': categories, 'rules': rules}
            sorted_rules = list(set(emp.contract_id.struct_id.rule_ids.ids + \
                           current_rule_ids))
            sorted_rules = self.env['hr.salary.rule'].browse(sorted_rules)
            for rule in sorted_rules:
                if rule.code in ('BASIC','HA','TA'):
                    sorted_rules_new.append(rule)
                if rule.category_id.code =='ALW' and rule not in sorted_rules_new:
                    sorted_rules_new.append(rule)
            localdict = dict(baselocaldict, employee=emp,
                             contract=emp.contract_id)
            count = 0
            all_alowances = 0.0
            for rule in sorted_rules_new:
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                if rule.satisfy_condition(localdict) and rule.id not in \
                        blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule.compute_rule(localdict)
                    count += amount
                    if rule.category_id.code == 'ALW':
                        all_alowances += amount
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the
                    # localdict
                    tot_rule = amount * qty * rate / 100.0
                    # if localdict.get(rule.code):
                    #     tot_rule += localdict.get(rule.code)
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict,
                                                          rule.category_id,
                                                          tot_rule -
                                                          previous_amount)
            localdict.update({'all_allowances': all_alowances})
            return localdict

    @api.model
    def get_data(self):
        """
        :return:
        """
        datas = []
        employee_rec = self.env['hr.employee'].browse(
            self._context.get('active_ids'))
        for emp_rec in employee_rec:
            grade = ''
            if emp_rec.contract_id and emp_rec.contract_id.grade_level:
                grade = emp_rec.contract_id.grade_level.name
            salary_data = self.salary_data(emp_rec)
            allowences = self.get_allowences_data(emp_rec)
            allowence = float(allowences.get('total', 0.0)) or 0.0
            basic = float(salary_data.get("BASIC", 0.0)) or 0.0
            housing = float(salary_data.get("HA", 0.0)) or 0.0
            transportation = float(salary_data.get("TA", 0.0)) or 0.0
            housing_ta = housing + transportation
            other_earnings = allowence - housing_ta
            total = float(basic) + float(housing) + float(
                transportation) + float(other_earnings)
            section = ''
            department = ''
            bussiness_unit = ''
            cost_center = ''
            if emp_rec.department_id:
                if emp_rec.department_id.org_unit_type == 'section':
                    section = emp_rec.department_id.name
                dept_rec = self._get_department(emp_rec.department_id)
                if dept_rec:
                    department = dept_rec.name
                bus_rec = self._get_business_unit(emp_rec.department_id)
                if bus_rec:
                    bussiness_unit = bus_rec.name
            if emp_rec.job_id and emp_rec.job_id.analytic_account_id:
                cost_center = emp_rec.job_id.analytic_account_id.code
            emp_data = {
                'employee_id': emp_rec.f_employee_no,
                'employee_name': emp_rec.name,
                'business_unit': bussiness_unit,
                'department': department,
                'section': section,
                'cost_center': cost_center,
                'date_of_joining': emp_rec.initial_employment_date,
                'nationality': emp_rec.country_id.name,
                'career_band_or_job': emp_rec.job_template_id.name,
                'grade': grade,
                'job_title': emp_rec.job_id.name,
                'current_base_salary': basic,
                'hosing_allowance': housing,
                'transportation': transportation,
                'other_earnings': other_earnings,
                'total': total,
            }
            datas.append(emp_data)
        return datas

    @api.model
    def set_line_data(self, worksheet, emp_data):
        """
        set line in excel report
        :param worksheet: excel object
        :return:
        """
        row_count = 1
        for data in emp_data:
            column_count = 0
            worksheet.write(row_count, column_count, data.get('employee_id'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('employee_name'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('business_unit'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('department'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('section'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('cost_center'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('date_of_joining'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('nationality'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('career_band_or_job'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('grade'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('job_title'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('current_base_salary'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('hosing_allowance'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('transportation'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('other_earnings'))
            column_count += 1
            worksheet.write(row_count, column_count, data.get('total'))
            column_count += 1
            row_count += 1


    @api.multi
    def generate_salary_summary(self):
        """
        Employee salary summary report
        :return:{}
        """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Employee Salary Sumary')
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 255, 160, 122)
        xlwt.add_palette_colour("h1_text_color", 0x22)
        workbook.set_colour_RGB(0x22, 204, 51, 0)
        xlwt.add_palette_colour("h2_text_color", 0x23)
        workbook.set_colour_RGB(0x23, 128, 25, 0)
        self.set_header(worksheet)
        employee_data = self.get_data()
        self.set_line_data(worksheet, employee_data)
        # Freeze column,row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(1)
        # worksheet.set_vert_split_pos(2)
        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['hr.employee.salary.summary.print.link'].create(
            {'name': 'Salary Summary.xls',
             'sal_summary_xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.employee.salary.summary.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
            }


class LoanReportPrintLink(models.Model):
    _name = 'hr.employee.salary.summary.print.link'

    sal_summary_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Salary Summary.xls')
