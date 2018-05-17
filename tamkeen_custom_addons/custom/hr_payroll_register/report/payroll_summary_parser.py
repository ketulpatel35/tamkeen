from odoo.report import report_sxw
from odoo import models, api
from odoo.api import Environment


class PayrollSummaryParser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(PayrollSummaryParser, self).__init__(cr,
                                                   uid,
                                                   name,
                                                   context=context)
        self.localcontext.update({
            'get_details_by_run': self.get_details_by_run,
        })

    def get_details_by_run(self, run_recs):
        res = []
        for run_rec in run_recs:
            subtotal = self.get_subtotal_by_payslip(run_rec.slip_ids)
            subtotal['name'] = run_rec.name
            res.append(subtotal)
        return res

    def get_subtotal_by_payslip(self, payslips):
        subtotal = {
            'name': '',
            'id_no': '',
            'salary': 0,
            'ot': 0,
            'transportation': 0,
            'allowances': 0,
            'taxable_gross': 0,
            'gross': 0,
            'fit': 0,
            'ee_pension': 0,
            'deductions': 0,
            'deductions_total': 0,
            'net': 0,
            'er_contributions': 0,
        }
        for slip in payslips:
            tmp = self.get_details_by_rule_category(
                slip.details_by_salary_rule_category)
            # Increase subtotal
            subtotal['salary'] += tmp['salary']
            subtotal['ot'] += tmp['ot']
            subtotal['transportation'] += tmp['transportation']
            subtotal['allowances'] += tmp['allowances']
            subtotal['gross'] += tmp['gross']
            subtotal['taxable_gross'] += tmp['taxable_gross']
            subtotal['fit'] += tmp['fit']
            subtotal['ee_pension'] += tmp['ee_pension']
            subtotal['deductions'] += tmp['deductions']
            subtotal['deductions_total'] += tmp['deductions_total']
            subtotal['net'] += tmp['net']
            subtotal['er_contributions'] += tmp['er_contributions']
        return subtotal

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
        # Choose only the categories (or rules) that we want to
        # show in the report.
        regline = {
            'name': '',
            'id_no': '',
            'salary': 0,
            'ot': 0,
            'transportation': 0,
            'allowances': 0,
            'taxable_gross': 0,
            'gross': 0,
            'fit': 0,
            'ee_pension': 0,
            'deductions': 0,
            'deductions_total': 0,
            'net': 0,
            'er_contributions': 0,
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
            for r in res:
                # Level 0 is the category
                if r['code'] == 'BASIC' and r['level'] == 0:
                    regline['salary'] = r['total']
                elif r['code'] == 'OT':
                    regline['ot'] = r['total']
                elif r['code'] == 'TRA' or r['code'] == 'TRVA':
                    regline['transportation'] = r['total']
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

            # Make adjustments to subtract from the parent category's total the
            # amount of individual rules that we show separately on the sheet.
            regline['allowances'] -= regline['transportation']
            regline['deductions'] -= regline['ee_pension']

            # Increase running totals

            # self.salary += regline.get('salary', 0)
            # self.ot += regline.get('ot', 0)
            # self.transportation += regline.get('transportation', 0)
            # self.allowances += regline.get('allowances', 0)
            # self.gross += regline.get('gross', 0)
            # self.taxable_gross += regline.get('taxable_gross', 0)
            # self.ded_fit += regline.get('fit', 0)
            # self.ded_pf_ee += regline.get('ee_pension', 0)
            # self.deduct += regline.get('deductions', 0)
            # self.total_deduct += regline.get('deductions_total', 0)
            # self.net += regline.get('net', 0)
            # self.er_contributions += regline.get('er_contributions', 0)

        return regline


class AbsPayrollSummaryParser(models.AbstractModel):
    _name = 'report.hr_payroll_register.report_payroll_summary_template'

    _inherit = 'report.abstract_report'

    _template = 'hr_payroll_register.report_payroll_summary_template'

    _wrapped_report_class = PayrollSummaryParser
