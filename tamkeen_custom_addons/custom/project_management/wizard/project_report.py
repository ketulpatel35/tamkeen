try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields, _
from cStringIO import StringIO
import base64
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import datetime


class Project(models.TransientModel):
    _name = 'project.project.report'

    @api.model
    def set_header(self, worksheet):
        """
           set header
           :param worksheet: excel sheet object
           :param period_id: object
           :return: updated excel sheet object
       """
        worksheet.row(0).height = 600
        for for_col in range(0, 3):
            worksheet.col(for_col).width = 256 * 20
        for for_col in range(0, 100):
            worksheet.col(for_col).width = 256 * 19
        s1 = xlwt.easyxf(
            'font: bold 1, height 260, colour h1_text_color;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        s2 = xlwt.easyxf(
            'font: bold 1,height 180 ,colour h2_text_color;'
            'alignment: horizontal center, wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        s3 = xlwt.easyxf(
            'font: bold 1, height 260, colour h1_text_color;'
            'alignment: horizontal center, wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        worksheet.write_merge(0, 0, 0, 0, 'Project Code', s2)
        worksheet.write_merge(0, 0, 1, 1, 'Project Name', s2)
        worksheet.write_merge(0, 0, 2, 2, 'Project SPI', s2)
        worksheet.write_merge(0, 0, 3, 3, 'Milestone Code', s2)
        worksheet.write_merge(0, 0, 4, 4, 'Milestone Name', s2)
        worksheet.write_merge(0, 0, 5, 5, 'Milestone Actual Cost (SAR)', s2)
        worksheet.write_merge(0, 0, 6, 6, 'Task Code', s2)
        worksheet.write_merge(0, 0, 7, 7, 'Task Name', s2)
        worksheet.write_merge(0, 0, 8, 8, 'Task Start Date', s2)
        worksheet.write_merge(0, 0, 9, 9, 'Task End Date', s2)
        worksheet.write_merge(0, 0, 10, 10, 'Task Duration (Days)', s2)
        worksheet.write_merge(0, 0, 11, 11, 'Task Responsibility', s2)
        worksheet.write_merge(0, 0, 12, 12, 'Task Completion %', s2)

    @api.model
    def get_milestone_report_line(self):
        """
        get milestone report line
        :return:
        """
        data = []
        project_ids = False
        if self._context and self._context.get('active_ids'):
            project_ids = self._context.get('active_ids')
        for project_rec in self.env['project.project'].browse(project_ids):
            for milestone in project_rec.milestones_schedule_ids:
                for task in milestone.task_ids:
                    start = False
                    end = False
                    duration = False
                    days = 0
                    if task.date_start:
                        start = str(datetime.datetime.strptime(task.date_start,
                                                               DEFAULT_SERVER_DATETIME_FORMAT).date())
                    if task.date_deadline:
                        end = task.date_deadline
                    if start and end:
                        duration =datetime.datetime.strptime(
                            task.date_deadline,DEFAULT_SERVER_DATE_FORMAT).date()\
                                  -datetime.datetime.strptime(task.date_start,DEFAULT_SERVER_DATETIME_FORMAT).date()
                        if duration:
                            days = duration.days
                    responsible = ''
                    if task.main_assignment =='internal':
                        responsible = task.user_id.name
                    if task.main_assignment == 'external':
                        responsible = task.assigned_to_external
                    data.append({
                        'project_code':task.project_id.code or '',
                        'project_name':task.project_id.name or '',
                        'project_spi': "%.2f"%task.project_id.spi or '',
                        'milestone_code': task.milestones_schedule_id.code or '',
                        'milestone_name': task.milestones_schedule_id.name
                                          or '',
                        'milestone_actual_cost':task.milestones_schedule_id
                            .estimated_value or '',
                        'task_code': task.code or '',
                        'task_name': task.name or '',
                        'task_start_date':start or '',
                        'task_end_date': end or '',
                        'task_duration':str(days or ''),
                        'task_responsible':responsible or '',
                        'task_completion':task.task_completion_progress or '',

                    })
        return data

    @api.model
    def set_line_data(self, worksheet):
        """
        set line in excel report
        :param worksheet: excel object
        :return:
        """
        task_details = self.get_milestone_report_line()
        row_count = 1
        for line in task_details:
            column_count = 0
            worksheet.write(row_count, column_count, line.get('project_code', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('project_name', ''))
            column_count += 1
            worksheet.write(row_count, column_count,line.get('project_spi', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('milestone_code', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('milestone_name', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('milestone_actual_cost', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('task_code', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('task_name', ''))
            column_count += 1
            worksheet.write(row_count, column_count, str(line.get('task_start_date', '')))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('task_end_date', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('task_duration', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('task_responsible', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('task_completion', ''))
            column_count += 1
            row_count += 1



    @api.multi
    def print_report(self):
        """
             Project Schedule xls Report
             :return: {}
             """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Project Schedule Report')
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 255, 160, 122)
        xlwt.add_palette_colour("h1_text_color", 0x22)
        workbook.set_colour_RGB(0x22, 204, 51, 0)
        xlwt.add_palette_colour("h2_text_color", 0x23)
        workbook.set_colour_RGB(0x23, 128, 25, 0)
        self.set_header(worksheet)
        self.set_line_data(worksheet)
        # Freeze column,row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(1)
        worksheet.set_vert_split_pos(5)
        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['project.project.report.print.link'].create(
            {'name': 'Project Schedule Report.xls',
             'project_xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.project.report.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }




class LoanReportPrintLink(models.Model):
    _name = 'project.project.report.print.link'

    project_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Project_Schedule_Report.xls')
