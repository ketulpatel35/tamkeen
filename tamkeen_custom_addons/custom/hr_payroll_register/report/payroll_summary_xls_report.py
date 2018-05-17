try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields, _
from cStringIO import StringIO
import base64


class PayslipSummaryReportXLS(models.Model):
    _name = 'payslip.summary.report.xls'

    LEVEL = 0
    TOTAL_LEVEL = []
    ROW_COUNT = 2
    # DEPT_IDS = []
    DISPLAY_LINE = []

    @api.model
    def set_header(self, worksheet, period_rec):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """
        worksheet.row(0).height = 600
        worksheet.row(1).height = 750
        for for_col in range(0, 10):
            if for_col in [0, 1, 2]:
                worksheet.col(for_col).width = 256 * 28
                worksheet.col(for_col).width = 256 * 28
            else:
                worksheet.col(for_col).width = 256 * 13
        s1 = xlwt.easyxf(
            'font: bold 1, height 260, colour h1_text_color;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour custom_gray,'
            'fore_colour custom_gray')
        s2 = xlwt.easyxf(
            'font: bold 1,height 180 ,colour h2_text_color;'
            'alignment: horizontal center, wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour custom_gray,'
            'fore_colour custom_gray'
        )
        header_0 = "Payroll Period Summary for : %s" % (period_rec.name)
        worksheet.write_merge(0, 0, 0, 3, header_0, s1)
        title_name = ['Parent Department', 'Department', 'Sub Department/s']
        if 'is_cost_center' in self.DISPLAY_LINE:
            title_name.append('Cost Center')
        if 'is_basic' in self.DISPLAY_LINE:
            title_name.append('Basic')
        if 'is_transport_allowance' in self.DISPLAY_LINE:
            title_name.append('Total Transport Allowance')
        if 'is_housing_allowance' in self.DISPLAY_LINE:
            title_name.append('Total Housing Allowance')
        if 'is_rate_allowance' in self.DISPLAY_LINE:
            title_name.append('Total Rare Allowance')
        if 'is_cost_of_living_allowance' in self.DISPLAY_LINE:
            title_name.append('Total Cost Of Living Allowance')
        if 'is_other_earnings' in self.DISPLAY_LINE:
            title_name.append('Total Other Earnings')
        if 'is_other_allowances' in self.DISPLAY_LINE:
            title_name.append('Total Earnings')
        if 'is_gosi_deduction' in self.DISPLAY_LINE:
            title_name.append('Total GOSI Deduction')
        if 'is_other_deductions' in self.DISPLAY_LINE:
            title_name.append('Total Other Deductions')
        if 'is_total_deductions' in self.DISPLAY_LINE:
            title_name.append('Total Deductions')
        if 'is_total_gross' in self.DISPLAY_LINE:
            title_name.append('Total Gross')
        if 'is_total_net_salary' in self.DISPLAY_LINE:
            title_name.append('Total Net Salary')
        row_count = 1
        col_count = 0
        for t_name in title_name:
            worksheet.write(row_count, col_count,
                            t_name, s2)
            col_count += 1

    @api.model
    def get_payslip_data(self, period_rec):
        """
        :return:
        """
        data_list = []
        payslip_obj = self.env['hr.payslip']
        period_payslip_ids = payslip_obj.search([
            ('date_from', '>=', period_rec.date_start),
            ('date_to', '<=', period_rec.date_end)])
        if period_payslip_ids:
            for slip in period_payslip_ids:
                data = {
                    'department_id':
                        slip.contract_id.employee_id.department_id.id,
                    'depat_name':
                        slip.contract_id.employee_id.department_id.name,
                    'BASIC': 0, 'BDED': 0, 'BNET': 0, 'HA': 0, 'HADED': 0,
                    'HANET': 0, 'TA': 0, 'TADED': 0, 'TANET': 0, 'CA': 0,
                    'CADED': 0, 'CANET': 0, 'RA': 0, 'RADED': 0, 'RANET': 0,
                    'FXDALW': 0, 'FXDALWDED': 0, 'FXDALWNET': 0, 'ADED': 0,
                    'ALW': 0, 'GOSI': 0, 'TDED': 0, 'ADED': 0, 'OT': 0,
                    'OE': 0, 'OD': 0, 'TTLERNG': 0, 'TTLDED': 0, 'GROSS': 0,
                    'NET': 0, 'note': '', 'CLANET': 0}
                total_allowance = total_deduction = 0
                for line in slip.line_ids:
                    if line.code == 'BASIC':
                        data.update({'BASIC': line.total})
                    if line.code == 'BDED':
                        data.update({'BDED': line.total})
                    if line.code == 'BNET':
                        data.update({'BNET': line.total})
                    if line.code == 'HA':
                        data.update({'HA': line.total})
                    if line.code == 'HADED':
                        data.update({'HADED': line.total})
                    if line.code == 'HANET':
                        data.update({'HANET': line.total})
                    if line.code == 'TA':
                        data.update({'TA': line.total})
                    if line.code == 'TADED':
                        data.update({'TADED': line.total})
                    if line.code == 'TANET':
                        data.update({'TANET': line.total})
                    if line.code == 'CA':
                        data.update({'CA': line.total})
                    if line.code == 'CADED':
                        data.update({'CADED': line.total})
                    if line.code == 'CANET':
                        data.update({'CANET': line.total})
                    if line.code == 'RA':
                        data.update({'RA': line.total})
                    if line.code == 'CLANET':
                        data.update({'CLANET': line.total})
                    if line.code == 'RADED':
                        data.update({'RADED': line.total})
                    if line.code == 'RANET':
                        data.update({'RANET': line.total})
                    if line.code == 'FXDALW':
                        data.update({'FXDALW': line.total})
                    if line.code == 'FXDALWDED':
                        data.update({'FXDALWDED': line.total})
                    if line.code == 'FXDALWNET':
                        data.update({'FXDALWNET': line.total})
                    if line.code == 'OT':
                        data.update({'OT': line.total})
                    if line.code == 'OE':
                        data.update({'OE': line.total})
                    if line.code == 'OD':
                        od_total = line.total
                        if od_total:
                            od_total = od_total * -1
                        data.update({'OD': od_total})
                    if line.note:
                        data.update({'note': line.note})
                    if line.category_id.code == 'ALW':
                        total_allowance += line.total
                    if line.category_id.code == 'DED':
                        total_deduction += line.total
                    if line.code == 'GOSI':
                        gosi_value = line.total
                        if gosi_value:
                            gosi_value = gosi_value * -1
                        data.update({'GOSI': gosi_value})
                    if line.code == 'GROSS':
                        data.update({'GROSS': line.total})
                    if line.code == 'NET':
                        data.update({'NET': line.total})
                TTLERNG = \
                    data['BNET'] + data['HANET'] \
                    + data['TANET'] + data['RANET'] + \
                    data['OE']
                if data.get('CLANET'):
                    TTLERNG += data['CLANET']
                ADED = total_deduction - data['BDED'] - data['HADED'] - \
                       data['TADED']
                if ADED:
                    ADED = ADED * -1
                if total_deduction:
                    total_deduction = total_deduction * -1
                data.update({
                    'TTLERNG': TTLERNG,
                    'TTLDED': data['GOSI'] + data['OD'],
                    'ALW': total_allowance - data['HA'] - data['TA'],
                    'TDED': total_deduction,
                    'ADED': ADED
                })
                data_list.append(data)
        return data_list

    def get_child_ids(self, parent_id):
        child_ids = self.env['hr.department'].search([
            ('parent_id', '=', parent_id)]).ids
        return child_ids

    def get_parent_name(self, child_id):
        if self.env['hr.department'].browse(child_id).parent_id:
            return self.env['hr.department'].browse(child_id).parent_id.name
        else:
            return False

    @api.model
    def get_department_leaf(self):
        dept_obj = self.env['hr.department']
        dept_with_lead = {}

        def _collect_leaf_nodes(root_id, leafs):
            if root_id:
                if not self.get_child_ids(root_id):
                    leafs.append(root_id)
                else:
                    leafs.append(root_id)
                for n in self.get_child_ids(root_id):
                    _collect_leaf_nodes(n, leafs)

        for dept_id in dept_obj.search([]):
            leafs = []
            _collect_leaf_nodes(dept_id.id, leafs)
            dept_with_lead.update({dept_id.id: leafs})
        return dept_with_lead

    @api.model
    def get_level(self, dept_id):
        dept_obj = self.env['hr.department']
        partner_rec = dept_obj.browse(dept_id).parent_id
        if partner_rec:
            self.get_level(partner_rec.id)
            self.LEVEL += 1
        if self.LEVEL not in self.TOTAL_LEVEL:
            self.TOTAL_LEVEL.append(self.LEVEL)
        return self.LEVEL

    @api.model
    def get_report_data(self, dept_with_leaf, payslip_data):
        single_line_data = []
        total_line_data = []
        single_report_data = {}
        total_report_data = {}
        for dept_id in dept_with_leaf:
            level = self.get_level(dept_id)
            self.LEVEL = 0
            default_vals = {
                'department_id': dept_id, 'level': level, 'depat_name':
                    self.env['hr.department'].browse(dept_id).name,
                'BASIC': 0, 'TA': 0, 'HA': 0, 'RA': 0, 'OE':0, 'ALW': 0,
                'GOSI': 0, 'TDED': 0, 'GROSS': 0, 'NET': 0, 'CLANET': 0}
            # for single department report
            single_report_data.update(default_vals)
            for slip_data in payslip_data:
                if slip_data['department_id'] == dept_id:
                    single_report_data['BASIC'] += slip_data['BASIC']
                    single_report_data['TA'] += slip_data['TA']
                    single_report_data['HA'] += slip_data['HA']
                    single_report_data['RA'] += slip_data['RA']
                    single_report_data['OE'] += slip_data['OE']
                    single_report_data['ALW'] += slip_data['ALW']
                    single_report_data['GOSI'] += slip_data['GOSI']
                    single_report_data['TDED'] += slip_data['TDED']
                    single_report_data['GROSS'] += slip_data['GROSS']
                    single_report_data['NET'] += slip_data['NET']
                    if slip_data.get('CLANET'):
                        single_report_data['CLANET'] += slip_data.get('CLANET')
            single_line_data.append(single_report_data)
            single_report_data = {}
            # for total report data
            total_report_data.update(default_vals)
            for leaf_dept_id in dept_with_leaf[dept_id]:
                for slip_data in payslip_data:
                    if slip_data['department_id'] == leaf_dept_id:
                        total_report_data['BASIC'] += slip_data['BASIC']
                        total_report_data['TA'] += slip_data['TA']
                        total_report_data['HA'] += slip_data['HA']
                        total_report_data['RA'] += slip_data['RA']
                        total_report_data['OE'] += slip_data['OE']
                        total_report_data['ALW'] += slip_data['ALW']
                        total_report_data['GOSI'] += slip_data['GOSI']
                        total_report_data['TDED'] += slip_data['TDED']
                        total_report_data['GROSS'] += slip_data['GROSS']
                        total_report_data['NET'] += slip_data['NET']
                        if slip_data.get('CLANET'):
                            single_report_data['CLANET'] += slip_data.get('CLANET')
            total_line_data.append(total_report_data)
            total_report_data = {}
        return single_line_data, total_line_data

    @api.model
    def get_lines_data(self, period_rec):
        """
        get line data
        :return:
        """
        dept_with_leaf = self.get_department_leaf()
        payslip_data = self.get_payslip_data(period_rec)
        single_line_data, total_line_data = self.get_report_data(
            dept_with_leaf, payslip_data)
        return single_line_data, total_line_data

    @api.model
    def write_level_line(self, worksheet, single_line_data, parent_line_data,
                         total_line_data):
        """
        :param worksheet:
        :param single_line_data:
        :param total_line_data:
        :return:
        """
        self.set_header_data(worksheet, parent_line_data)
        self.set_sub_data(worksheet, parent_line_data.get('department_id'),
                          single_line_data, True)
        self.set_sub_data(worksheet, parent_line_data.get('department_id'),
                          total_line_data, False)

    @api.model
    def set_sub_data(self, worksheet, dept_id, line_data, own=False):
        """
        set line data
        :param worksheet:
        :param line_data:
        :return:
        """
        if own:
            department_ids = [dept_id]
            run_datas = filter(lambda x: x['department_id'] in department_ids,
                               line_data)
        else:
            department_ids = self.get_child_ids(dept_id)
            run_datas = filter(lambda x: x['department_id'] in department_ids,
                               line_data)
        for run_data in run_datas:
            row_c = self.ROW_COUNT
            col_c = 2
            worksheet.write(row_c, col_c, run_data.get('depat_name', ''))
            col_c += 1
            if 'is_cost_center' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c, '-')
                col_c += 1
            if 'is_basic' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c, float(run_data.get('BASIC', 0)))
                col_c += 1
            if 'is_transport_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c, float(run_data.get('TA', 0)))
                col_c += 1
            if 'is_housing_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c, float(run_data.get('HA', 0)))
                col_c += 1
            if 'is_rate_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c, float(run_data.get('RA', 0)))
                col_c += 1
            if 'is_cost_of_living_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('CLANET', 0)))
                col_c += 1
            if 'is_other_earnings' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('OE', 0)))
                col_c += 1
            if 'is_other_allowances' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('TTLERNG', 0)))
                col_c += 1
            if 'is_gosi_deduction' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('GOSI', 0)))
                col_c += 1
            if 'is_other_deductions' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('OD', 0)))
                col_c += 1
            if 'is_total_deductions' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('TDED', 0)))
                col_c += 1
            if 'is_total_gross' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('GROSS', 0)))
                col_c += 1
            if 'is_total_net_salary' in self.DISPLAY_LINE:
                worksheet.write(row_c, col_c,
                                float(run_data.get('NET', 0)))
                col_c += 1
            self.ROW_COUNT += 1

    @api.model
    def set_header_data(self, worksheet, parent_line_data):
        row_count = self.ROW_COUNT
        s1 = xlwt.easyxf(
            'font: bold 1, colour custom_blue;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour light_gray,'
            'fore_colour light_gray;'
            'alignment: horizontal center;')
        s2 = xlwt.easyxf(
            'font: bold 1, colour custom_blue;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour light_gray,'
            'fore_colour light_gray;')
        if parent_line_data:
            run_data = parent_line_data
            col_c = 0
            child_ids = self.get_child_ids(run_data.get('department_id'))
            mearge_row = row_count + len(child_ids) + 2
            parent_name = self.get_parent_name(parent_line_data.get(
                'department_id')) or '-'
            for row_c in range(row_count, mearge_row):
                worksheet.write(row_c, col_c, parent_name, s1)
            col_c += 1
            for row_c in range(row_count, mearge_row):
                worksheet.write(row_c, col_c, run_data.get('depat_name', ''),
                                s1)
            col_c += 1
            worksheet.write(row_count, col_c, '+', s1)
            col_c += 1
            if 'is_cost_center' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c, '-', s2)
                col_c += 1
            if 'is_basic' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('BASIC', 0)), s2)
                col_c += 1
            if 'is_transport_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('TA', 0)), s2)
                col_c += 1
            if 'is_housing_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('HA', 0)), s2)
                col_c += 1
            if 'is_rate_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('RA', 0)), s2)
                col_c += 1
            if 'is_cost_of_living_allowance' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('CLANET', 0)), s2)
                col_c += 1
            if 'is_other_earnings' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('OE', 0)), s2)
                col_c += 1
            if 'is_other_allowances' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('TTLERNG', 0)), s2)
                col_c += 1
            if 'is_gosi_deduction' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('GOSI', 0)), s2)
                col_c += 1
            if 'is_other_deductions' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('OD', 0)), s2)
                col_c += 1
            if 'is_total_deductions' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('TDED', 0)), s2)
                col_c += 1
            if 'is_total_gross' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('GROSS', 0)), s2)
                col_c += 1
            if 'is_total_net_salary' in self.DISPLAY_LINE:
                worksheet.write(row_count, col_c,
                                float(run_data.get('NET', 0)), s2)
                col_c += 1
            self.ROW_COUNT += 1

    @api.model
    def print_payslip_summary_xls_report(self, period_rec, fields_to_display):
        """
       Attendance xls Report
       :return: {}
       """
        workbook = xlwt.Workbook()
        self.DISPLAY_LINE = fields_to_display
        worksheet = workbook.add_sheet('Payslip Summary')
        xlwt.add_palette_colour("custom_gray", 0x21)
        workbook.set_colour_RGB(0x21, 150, 150, 150)
        xlwt.add_palette_colour("h1_text_color", 0x22)
        workbook.set_colour_RGB(0x22, 204, 51, 0)
        xlwt.add_palette_colour("h2_text_color", 0x23)
        workbook.set_colour_RGB(0x23, 128, 25, 0)
        xlwt.add_palette_colour("light_gray", 0x24)
        workbook.set_colour_RGB(0x24, 224, 224, 224)
        xlwt.add_palette_colour("custom_blue", 0x25)
        workbook.set_colour_RGB(0x25, 51, 51, 255)
        self.set_header(worksheet, period_rec)
        single_line_data, total_line_data = self.get_lines_data(period_rec)
        with_child = True if 'is_has_no_child' in self.DISPLAY_LINE else False
        for level in self.TOTAL_LEVEL:
            for parent_line_data in filter(lambda x: x['level'] == level,
                                           total_line_data):
                if with_child:
                    self.write_level_line(worksheet, single_line_data,
                                          parent_line_data, total_line_data)
                else:
                    if len(self.get_child_ids(parent_line_data.get(
                            'department_id'))) > 0:
                        self.write_level_line(worksheet, single_line_data,
                                              parent_line_data,
                                              total_line_data)
        # Freeze column,row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(2)
        worksheet.set_vert_split_pos(4)
        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['payslip.summary.dow'].create(
            {'name': 'Payslip Summary.xls',
             'payslip_summary_xls_output': base64.encodestring(
                 stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payslip.summary.dow',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'}


class PayslipSummaryDOW(models.Model):
    _name = 'payslip.summary.dow'

    payslip_summary_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Payslip Summary.xls')
