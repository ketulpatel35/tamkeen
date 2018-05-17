from odoo.report import report_sxw
from odoo import models, api
from odoo.api import Environment
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from datetime import datetime


class PayslipParser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(PayslipParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_details_by_payslip': self.get_details_by_payslip,
        })
        self.env = Environment(cr, uid, context)
        self.no = 0
        self.salary = 0.0
        self.ot = 0.0
        self.transportation = 0.0
        self.allowances = 0.0
        self.gross = 0.0
        self.taxable_gross = 0.0
        self.ded_fit = 0.0
        self.ded_pf_ee = 0.0
        self.deduct = 0.0
        self.total_deduct = 0.0
        self.net = 0.0
        self.er_contributions = 0.0
        self.saved_run_id = -1

    # @api.model
    # def get_payslip_accruals(self, contract_ids, dToday):
    #     """
    #     :param contract_ids:
    #     :param dToday:
    #     :return:
    #     """
    #     accrual_policy_obj = self.env['hr.policy.accrual']
    #     contract_obj = self.env['hr.contract']
    #     res = []
    #     for contract_rec in contract_obj.browse(contract_ids):
    #         policy = accrual_policy_obj.get_latest_policy(
    #             contract_rec.policy_group_id,
    #             dToday)
    #         if policy is None:
    #             continue
    #         for accrual_policy_line in policy.line_ids:
    #             if accrual_policy_line.balance_on_payslip \
    #                     and accrual_policy_line.accrual_id.id not in res:
    #                 res.append((accrual_policy_line.accrual_id.id,
    #                             accrual_policy_line.accrual_id.
    #                             holiday_status_id.code))
    #     return res

    @api.model
    def get_details_by_payslip(self, payslips):
        # self.env = Environment(
        #     payslips._cr, payslips._uid, payslips._context)
        # accrual_obj = self.env['hr.accrual']
        res = []
        for slip in payslips.slip_ids:
            tmp, contract_ids = self.get_details_by_rule_category(
                slip.details_by_salary_rule_category)
            tmp['name'] = slip.employee_id.name
            tmp['id_no'] = slip.employee_id.identification_id
            tmp['date_from'] = slip.date_from
            tmp['date_to'] = slip.date_to
            dToday = datetime.strptime(slip.date_from, OE_DATEFORMAT).date()
            # accruals = self.get_payslip_accruals(contract_ids, dToday)
            holiday_status_id = self.env['hr.holidays.status'].search([(
                'code', '=', 'ANNLV')])
            # if len(accruals) > 0:
            #     for accrual_id, code in accruals:
            balance = self.env['hr.holidays']._get_employee_balance(
                holiday_status_id, slip.employee_id)
                    # balance = accrual_obj.browse(accrual_id).get_balance(
                    #     slip.employee_id.id, slip.date_to)
            balance = balance.get('current_employee_balance')
            tmp['ANNLV'] = balance
            res.append(tmp)
        return res

    @api.model
    def get_details_by_rule_category(self, obj):
        self.env = Environment(
            obj._cr, obj._uid, obj._context)
        payslip_line = self.env['hr.payslip.line']
        rule_cate_obj = self.env['hr.salary.rule.category']

        def get_recursive_parent(rule_categories):
            if not rule_categories:
                return []
            if rule_categories[0].parent_id:
                rule_categories.insert(0, rule_categories[0].parent_id)
                get_recursive_parent(rule_categories)
            return rule_categories
        res = []
        result = {}
        ids = []
        contract_ids = []
        # Choose only the categories (or rules) that we want to
        # show in the report.
        regline = {
            'salary': 0,
            'ot': 0,
            'transportation': 0,
            'bonus': 0,
            'allowances': 0,
            'taxable_gross': 0,
            'gross': 0,
            'fit': 0,
            'ee_pension': 0,
            'deductions': 0,
            'deductions_total': 0,
            'net': 0,
            'er_contributions': 0,
            'LVANNUAL': 0,
        }
        # Arrange the Pay Slip Lines by category
        for id in range(len(obj)):
            ids.append(obj[id].id)
        if ids:
            self.cr.execute('''
            SELECT pl.id, pl.category_id FROM hr_payslip_line as pl \
                LEFT JOIN hr_salary_rule_category AS rc on \
                (pl.category_id = rc.id) \
                WHERE pl.id in %s \
                GROUP BY rc.parent_id, pl.sequence, pl.id, pl.category_id \
                ORDER BY pl.sequence, rc.parent_id''', (tuple(ids),))
            for x in self.cr.fetchall():
                result.setdefault(x[1], [])
                result[x[1]].append(x[0])
            for key, value in result.iteritems():
                rule_categories = rule_cate_obj.browse([key])
                parents = get_recursive_parent(rule_categories)
                category_total = 0
                for line in payslip_line.browse(value):
                    category_total += line.total
                level = 0
                for parent in parents:
                    res.append({
                        'rule_category': parent.name,
                        'name': parent.name,
                        'code': parent.code,
                        'level': level,
                        'total': category_total,
                    })
                    level += 1
                for line in payslip_line.browse(value):
                    res.append({
                        'rule_category': line.name,
                        'name': line.name,
                        'code': line.code,
                        'total': line.total,
                        'level': level
                    })
                    if line.contract_id.id not in contract_ids:
                        contract_ids.append(line.contract_id.id)
            for r in res:
                # Level 0 is the category
                if r['code'] == 'BASIC' and r['level'] == 0:
                    regline['salary'] = r['total']
                elif r['code'] == 'OT':
                    regline['ot'] = r['total']
                elif r['code'] == 'TRA' or r['code'] == 'TRVA':
                    regline['transportation'] = r['total']
                elif r['code'] in ['BONUS', 'PI', 'BUNCH']:
                    regline['bonus'] = r['total']
                elif r['code'] == 'ALW':
                    regline['allowances'] = r['total']
                elif r['code'] == 'TXBL':
                    regline['taxable_gross'] = r['total']
                elif r['code'] == 'GROSS':
                    regline['gross'] = r['total']
                elif r['code'] == 'FITCALC':
                    regline['fit'] = r['total']
                elif r['code'] == 'PENFEE':
                    regline['ee_pension'] = r['total']
                elif r['code'] == 'DED':
                    regline['deductions'] = r['total']
                elif r['code'] == 'DEDTOTAL':
                    regline['deductions_total'] = r['total']
                elif r['code'] == 'NET':
                    regline['net'] = r['total']
                elif r['code'] == 'ER':
                    regline['er_contributions'] = r['total']
                elif r['code'] == 'LVANNUAL':
                    regline['LVANNUAL'] = r['total']
            # Make adjustments to subtract from the parent category's total the
            # amount of individual rules that we show separately on the sheet.
            regline['allowances'] -= regline['transportation']
            regline['allowances'] -= regline['bonus']
            regline['deductions'] -= regline['ee_pension']
        return regline, contract_ids


class AbsPayslipParser(models.AbstractModel):
    _name = 'report.hr_payroll_register.report_payslips_template'

    _inherit = 'report.abstract_report'

    _template = 'hr_payroll_register.report_payslips_template'

    _wrapped_report_class = PayslipParser
