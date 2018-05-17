try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields, _
from odoo import tools
import time
from cStringIO import StringIO
import base64
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class CostCenterReportXls(models.TransientModel):
    _name = 'cost.center.report.xls'

    date_from = fields.Date(string='Date From',
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To')
    cost_center_ids = fields.Many2many('account.analytic.account',
                                       'cost_center_report_budget_rel',
                                       'cost_id', 'account_id',
                                       string='Analytic Accounts')
    budget_type = fields.Selection([
        ('cost', 'Cost'),
        ('revenue', 'Revenue'),
        ('costrevenue', 'Cost And Revenue'),
    ], 'Budget Type', required=True, default='cost')

    @api.onchange('date_from', 'date_to')
    def onchange_date_from(self):
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                self.date_to = False
                raise \
                    Warning(
                        _('Date from must be earlier than Date to.'))

    @api.model
    def set_header(self, worksheet):
        """
        :param worksheet:
        :return:
        """
        worksheet.row(0).height = 600
        worksheet.row(1).height = 750
        for for_col in range(0, 7):
            if for_col != 0:
                worksheet.col(for_col).width = 256 * 25
        s1 = xlwt.easyxf(
            'font: bold 1, height 260, colour h1_text_color;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        s4 = xlwt.easyxf(
            'font: bold 1,height 180 ,colour h2_text_color;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        header_0 = "Cost Centre Report from %s to %s" % (self.date_from,
                                                         self.date_to)
        worksheet.write_merge(0, 0, 0, 6, header_0, s1)
        worksheet.write(1, 0, 'NO', s4)
        worksheet.write(1, 1, 'Financial Account', s4)
        worksheet.write(1, 2, 'Analytic/cc', s4)
        worksheet.write(1, 3, 'Alloweded Budget', s4)
        worksheet.write(1, 4, 'Actual', s4)
        worksheet.write(1, 5, 'Commited', s4)
        worksheet.write(1, 6, 'Remianing', s4)

    @api.model
    def get_lines(self):
        """
        :param worksheet:
        :return:
        """
        date_from = self.date_from
        date_to = self.date_to
        analytic_line = self.env['account.analytic.line']
        analytic_ids = []
        analytic_obj = self.env['account.analytic.account']
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        if self.cost_center_ids:
            domain += [('account_id', 'in', self.cost_center_ids.ids)]
            analytic_ids = self.cost_center_ids.ids
        else:
            analytic_ids = analytic_obj.search([]).ids
        if self.budget_type == 'cost':
            domain += [('amount', '<', 0)]
        if self.budget_type == 'revenue':
            domain += [('amount', '>', 0)]
        line_data = analytic_line.search(domain)
        vals_for_filtered = {}

        for data in line_data:
            commited_amount = 0.0
            amount = 0
            line_vals = {
                'general_account_id': data.general_account_id,
                'analytic_account_id': data.account_id,
            }
            if data.general_account_id.id not in vals_for_filtered:
                if not any(val.get('analytic_account_id', False) ==
                                   data.account_id for val in
                           vals_for_filtered.get(data.general_account_id.id,
                                                 [])):
                    if data.account_id:
                        for line in data.account_id.crossovered_budget_line:
                            line_date_from = datetime.strptime(line.date_from,
                                                               '%Y-%m-%d').date().strftime(
                                DEFAULT_SERVER_DATE_FORMAT)
                            line_date_to = datetime.strptime(line.date_to,
                                                             '%Y-%m-%d').date().strftime(
                                DEFAULT_SERVER_DATE_FORMAT)
                            if line.crossovered_budget_id.state in ['validate',
                                                                    'done'] and \
                                                    date_from <= line_date_from <= \
                                            date_to or \
                                                    date_from <= line_date_to <= date_to:
                                if self.budget_type == 'cost' and line.planned_amount < 0:
                                    amount += line.planned_amount
                                elif self.budget_type == 'revenue' and line.planned_amount > 0:
                                    amount += line.planned_amount
                                elif self.budget_type == 'costrevenue':
                                    amount += line.planned_amount
                    pr_obj = self.env['purchase.requisition'].search(
                        [('create_date', '>=', date_from),
                         ('create_date', '<=', date_to),
                         ('account_analytic_id', '=', data.account_id.id),
                         ('state', 'not in', ('draft', 'tomanager_app',
                                              'procurement_review', 'vp'))])
                    for pr in pr_obj:
                        commited_amount += pr.commited_budget

                if data.general_account_id.id not in vals_for_filtered:
                    line_vals['allowed'] = amount
                    line_vals['actual'] = data.amount
                    line_vals['committed'] = commited_amount
                    vals_for_filtered[data.general_account_id.id] = [line_vals]
                elif data.general_account_id.id in vals_for_filtered:
                    if any(val.get('analytic_account_id', False) ==
                                   data.account_id for val in
                           vals_for_filtered.get(data.general_account_id.id,
                                                 [])):
                        for val in vals_for_filtered[
                            data.general_account_id.id]:
                            if val['analytic_account_id'] == data.account_id:
                                old_actual = val['actual']
                                val['actual'] = old_actual + data.amount
                    else:
                        line_vals['allowed'] = amount
                        line_vals['actual'] = data.amount
                        line_vals['committed'] = commited_amount
                        vals_for_filtered[data.general_account_id.id].append(
                            line_vals)
                else:
                    line_vals['allowed'] = amount
                    line_vals['actual'] = data.amount
                    line_vals['committed'] = commited_amount
                    vals_for_filtered[data.general_account_id.id].append(
                        line_vals)
            else:
                if any(val.get('analytic_account_id', False) ==
                               data.account_id for val in
                       vals_for_filtered.get(data.general_account_id.id,
                                             [])):
                    for val in vals_for_filtered[data.general_account_id.id]:
                        if val['analytic_account_id'] == data.account_id:
                            old_actual = val['actual']
                            val['actual'] = old_actual + data.amount
                else:
                    line_vals['allowed'] = amount
                    line_vals['actual'] = data.amount
                    line_vals['committed'] = commited_amount
                    vals_for_filtered[data.general_account_id.id].append(
                        line_vals)

        # check for PR
        def check_in_vals_for_filtered(analytic_id):
            for filtered_rec in vals_for_filtered:
                for rec in vals_for_filtered[filtered_rec]:
                    if rec.get('analytic_account_id').id == analytic_id:
                        return True
            return False

        remaining_analytic_id = [analytic_id for analytic_id in analytic_ids
                                 if not check_in_vals_for_filtered(
                analytic_id)]
        rem_count = 0
        for rem_analytic_rec in analytic_obj.browse(remaining_analytic_id):
            rem_amount = 0
            for line in rem_analytic_rec.crossovered_budget_line:
                line_from = datetime.strptime(line.date_from, '%Y-%m-%d').\
                    date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                line_to = datetime.strptime(line.date_to, '%Y-%m-%d').\
                    date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                if line.crossovered_budget_id.state in ['validate', 'done'] \
                        and date_from <= line_from <= date_to or \
                                        date_from <= line_to <= date_to:
                    if self.budget_type == 'cost' and line.planned_amount < 0:
                        rem_amount += line.planned_amount
                    elif self.budget_type == 'revenue' and \
                                    line.planned_amount > 0:
                        rem_amount += line.planned_amount
                    elif self.budget_type == 'costrevenue':
                        rem_amount += line.planned_amount

            pr_recs = self.env['purchase.requisition'].search(
                [('create_date', '>=', date_from),
                 ('create_date', '<=', date_to),
                 ('account_analytic_id', '=', rem_analytic_rec.id),
                 ('state', 'not in', ('draft', 'tomanager_app',
                                      'procurement_review', 'vp'))])
            pr_committed = 0
            for pr_rec in pr_recs:
                pr_committed += pr_rec.commited_budget
            name = 'x%s' % (rem_count)
            vals_for_filtered.update({
                name: [{
                    'general_account_id': False,
                    'analytic_account_id': rem_analytic_rec,
                    'allowed': rem_amount,
                    'actual' : 0,
                    'committed': pr_committed,
                }]})
            rem_count += 1
        return vals_for_filtered

    @api.model
    def set_lines(self, worksheet, vals_for_filtered):
        row_count = 2
        s3 = xlwt.easyxf(
            'alignment: horizontal left;'
            'font: bold 1;')
        s5 = xlwt.easyxf(
            'font: bold 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour custom_yellow,'
            'fore_colour custom_yellow')

        if self.budget_type == 'cost':
            worksheet.write_merge(row_count, row_count, 0, 6, 'Cost', s5)
        elif self.budget_type == 'revenue':
            worksheet.write_merge(row_count, row_count, 0, 6, 'Revenue', s5)
        row_count += 1
        col = 0
        count = 0
        if self.budget_type == 'cost':
            for value in vals_for_filtered.values():
                for val in value:
                    if val['allowed'] < 0:
                        total = 0
                        count += 1
                        worksheet.write(row_count, col, tools.ustr(count))
                        col += 1
                        if val['general_account_id']:
                            worksheet.write(row_count, col,
                                            tools.ustr(
                                                val['general_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col,
                                        tools.ustr(
                                            val['analytic_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col,
                                        tools.ustr(abs(val['allowed'])))
                        total = abs(val['allowed'])
                        col += 1
                        worksheet.write(row_count, col,
                                        tools.ustr(abs(val['actual'])))
                        total -= abs(val['actual'])
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'committed'])))
                        total -= abs(val['committed'])
                        col += 1
                        worksheet.write(row_count, col, total)
                        col = 0
                        row_count += 1
        elif self.budget_type == 'revenue':
            for value in vals_for_filtered.values():
                for val in value:
                    if val['allowed'] >= 0:
                        total = 0
                        count += 1
                        worksheet.write(row_count, col, tools.ustr(count))
                        col += 1
                        if val['general_account_id']:
                            worksheet.write(row_count, col,
                                            tools.ustr(
                                                val['general_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col,
                                        tools.ustr(
                                            val['analytic_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'allowed'])))
                        total += abs(val['allowed'])
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'actual'])))
                        total -= abs(val['actual'])
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'committed'])))
                        total -= abs(val['committed'])
                        col += 1
                        worksheet.write(row_count, col, total)
                        col = 0
                        row_count += 1
        elif self.budget_type == 'costrevenue':
            worksheet.write(row_count, col, 'Cost', s3)
            row_count += 1
            col = 0
            for value in vals_for_filtered.values():
                for val in value:
                    if val['allowed'] < 0:
                        total = 0
                        count += 1
                        worksheet.write(row_count, col, tools.ustr(count))
                        col += 1
                        if val['general_account_id']:
                            worksheet.write(row_count, col,
                                            tools.ustr(
                                                val['general_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col,
                                        tools.ustr(
                                            val['analytic_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'allowed'])))
                        total += abs(val['allowed'])
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'actual'])))
                        total -= abs(val['actual'])
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'committed'])))
                        total -= abs(val['committed'])
                        col += 1
                        worksheet.write(row_count, col, total)
                        col = 0
                        row_count += 1
            worksheet.write(row_count, col, 'Revenue', s3)
            row_count += 1
            col = 0
            for value in vals_for_filtered.values():
                for val in value:
                    if val['allowed'] >= 0:
                        total = 0
                        count += 1
                        worksheet.write(row_count, col, tools.ustr(count))
                        col += 1
                        if val['general_account_id']:
                            worksheet.write(row_count, col,
                                            tools.ustr(
                                                val['general_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col,
                                        tools.ustr(
                                            val['analytic_account_id'].name))
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'allowed'])))
                        total += abs(val['allowed'])
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'actual'])))
                        total -= abs(val['actual'])
                        col += 1
                        worksheet.write(row_count, col, tools.ustr(abs(val[
                                                                           'committed'])))
                        total -= abs(val['committed'])
                        col += 1
                        worksheet.write(row_count, col, total)
                        col = 0
                        row_count += 1
        return worksheet

    @api.multi
    def print_cost_report(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Cost Center Report')
        xlwt.add_palette_colour("custom_yellow", 0x21)
        workbook.set_colour_RGB(0x21, 250, 250, 150)
        xlwt.add_palette_colour("h1_text_color", 0x22)
        workbook.set_colour_RGB(0x22, 204, 51, 0)
        xlwt.add_palette_colour("h2_text_color", 0x23)
        workbook.set_colour_RGB(0x23, 128, 25, 0)
        self.set_header(worksheet)
        line_data = self.get_lines()
        self.set_lines(worksheet, line_data)
        # Freeze column,row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(2)

        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['cost.center.report.print.link'].create(
            {'name': 'Cost Center Report.xls',
             'cost_center_xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cost.center.report.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class AttReportPringLink(models.Model):
    _name = 'cost.center.report.print.link'

    cost_center_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Cost_Center_Report.xls')
