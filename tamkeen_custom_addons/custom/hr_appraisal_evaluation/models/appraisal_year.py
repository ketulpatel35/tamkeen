# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _


class appraisal_year_master(models.Model):
    _name = 'appraisal.year.master'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _description = 'Here You can Define the Apprisal Year for the Employees ' \
                   'that are going to have their Appraisal in the period ' \
                   'that you define in here'
    _rec_name = 'title'

    state = fields.Selection([('draft', 'Draft'),
                              ('pending_appraisal', 'Pending Appraisal'),
                              ('generated_appraisal', 'Appraisal Generated'),
                              ('cancel', 'Cancal'),
                              ('close', 'Closed')],
                             default='draft')
    title = fields.Char('Appraisal Title')
    type = fields.Selection([('quarterly', 'Quarterly'),
                             ('half_yearly', 'Half Yearly'),
                             ('yearly', 'Yearly')],
                            string='Type')
    app_from_date = fields.Date(string='From Date')
    app_to_date = fields.Date(string='To Date')
    emp_appraisal_line_ids = fields.One2many('hr.employee.appraisal.line',
                                             'appraisal_id',
                                             string='Employees')
    is_current_year = fields.Boolean('Is Current Year', default=True)

    @api.multi
    def generated_appraisal(self):
        emp_appraissal_obj = self.env['employee.appraisal']
        emp_obj_list = []
        period_from = self.app_from_date
        period_to = self.app_to_date
        counter = 0
        if len(self.emp_appraisal_line_ids) > 0:
            behaviour_rec = self.env['behaviour.types'].search([])
            behaviour_data_list = []
            for brec in behaviour_rec:
                ex_level = brec.expected_level.id or False
                behaviour_data = {
                    'name': brec.id,
                    'region': brec.region,
                    'expected_level': ex_level,
                    'definaition': brec.defination,
                    'weightage': brec.weightage,
                }
                behaviour_data_list.append((0, 0, behaviour_data))
            # Manager objective and behaviour
            req_cats_manager = self.env['requirement.category'].search([
                ('type', '=', 'manager')])
            objective_manager = req_cats_manager.filtered(
                lambda s: s.category_type == '1').Weightage
            behaviour_manager = req_cats_manager.filtered(
                lambda s: s.category_type == '2').Weightage
            # Employee objective and behaviour
            req_cats_employee = self.env['requirement.category'].search([
                ('type', '=', 'employee')])
            objective_employee = req_cats_employee.filtered(
                lambda s: s.category_type == '1').Weightage
            behaviour_employee = req_cats_employee.filtered(
                lambda s: s.category_type == '2').Weightage

            for emp_app_line in self.emp_appraisal_line_ids:
                emp_objective_obj = \
                    self.env['employee.objective']\
                        .search([('employee_id', '=',
                                  emp_app_line.emp_id.id), ('state', '=',
                                                            'mutual_agreed')],
                                limit=1)
                if emp_objective_obj:
                    for emp_obj_line in emp_objective_obj.emp_obj_line_ids:
                        emp_obj_vals = {
                            'temp_objective': 'test',
                            'kpi_measurement':
                                [(6, 0, emp_obj_line.kpi_measurement_ids.ids)],
                            'kpi_description':
                                emp_obj_line.obj_std_description,
                            'weightage': emp_obj_line.weightage,
                        }
                        emp_obj_list.append((0, 0, emp_obj_vals))
            for employee in self.emp_appraisal_line_ids:
                if employee.parent_id and employee.upper_manager \
                        and employee.department_id and employee.job_id \
                        and employee.state == 'pending':
                    manager = employee.emp_id.manager
                    objective_weightage = 0.0
                    behaviour_total_weightage = 0.0
                    obj_total_weightage = 0.0
                    if manager:
                        objective_weightage = objective_manager
                        behaviour_total_weightage = behaviour_manager
                    if not manager:
                        objective_weightage = objective_employee
                        behaviour_total_weightage = behaviour_employee
                    obj_total_weightage = \
                        objective_weightage + behaviour_total_weightage

                    vals = {
                        "emp_id": employee.emp_id.id,
                        "emo_no": employee.emp_no,
                        "immediate_manager": employee.parent_id.id,
                        "to_upper_manager": employee.upper_manager.id,
                        "appraisal_term": self.type,
                        "job_title": employee.job_id.id,
                        "date_of_joining": employee.initial_employment_date,
                        "department_id": employee.department_id.id,
                        "section": employee.employee_role,
                        "period_from": period_from,
                        "period_to": period_to,
                        "objective_weightage": objective_weightage,
                        "behaviour_total_weightage": behaviour_total_weightage,
                        "obj_total_weightage": obj_total_weightage,
                        "behaviour_comp": behaviour_data_list,
                        "appraisal_year_id": self.id,
                        'objective': emp_obj_list,
                        "career_discussion": [
                            (0, 0, {'career_discusion': '1'}),
                            (0, 0, {'career_discusion': '2'})],
                    }
                    emp_appraissal_obj.with_context(
                        {'const_app': True}).create(
                        vals)
                    employee.state = 'done'
        for rec in self.mapped('emp_appraisal_line_ids'):
            if rec.state == 'done':
                counter += 1

        if counter == len(self.mapped('emp_appraisal_line_ids').ids):
            self.write({'state': 'generated_appraisal'})
        else:
            self.write({'state': 'pending_appraisal'})

    @api.multi
    def cancel_appraisal(self):
        self.write({
            'state': 'cancel',
            'is_current_year': False,
        })

    @api.multi
    def close(self):
        self.write({
            'state': 'close',
            'is_current_year': False,
        })

    @api.multi
    @api.onchange('app_from_date', 'type')
    def onchange_calculate_appraisal_term(self):
        if self.app_from_date and type:
            from_date = datetime.strptime(self.app_from_date, '%Y-%m-%d')
            quater_month = relativedelta(months=3)
            half_yearly = relativedelta(months=6)
            yearly = relativedelta(months=12)
            if self.type == 'quarterly':
                to_date = from_date + quater_month
                self.app_to_date = to_date - timedelta(days=1)

            elif self.type == 'half_yearly':
                to_date = from_date + half_yearly
                self.app_to_date = to_date - timedelta(days=1)
            else:
                to_date = from_date + yearly
                self.app_to_date = to_date - timedelta(days=1)

    def get_employees(self):
        employee_record = self.env['hr.employee'].search([])
        emp_list = []
        for emp_rec in employee_record:
            record = {
                'emp_id': emp_rec.id,
                'parent_id': emp_rec.parent_id.id,
                'department_id': emp_rec.department_id.id,
                'job_id': emp_rec.job_id.id,
                'employee_role': emp_rec.employee_role,
                'manager': emp_rec.manager,
                'initial_employment_date': emp_rec.initial_employment_date, }
            emp_list.append((0, 0, record))
            self.write({'emp_appraisal_line_ids': emp_list})

    def email_notification(self):
        ir_model_data = self.env['ir.model.data']
        att = self.env['ir.attachment']. \
            search([('res_model', '=', 'appraisal.year.master')], limit=1)
        emp_emails = []
        for rec in self:
            for line in rec.emp_appraisal_line_ids:
                if line.state == 'done':
                    emp_emails.append(line.emp_id.user_id.partner_id.id)
        if emp_emails:
            try:
                template_id = ir_model_data.get_object_reference(
                    'hr_appraisal_evaluation',
                    'email_template_emp_appraisal')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(
                    'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict(self.env.context or {})
            ctx.update({
                'default_model': 'appraisal.year.master',
                'default_partner_ids': emp_emails,
                'default_from': self._uid or 'noreply@localhost',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_attachment_ids': att.ids,
                'default_composition_mode': 'comment',
            })
            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }

    @api.multi
    def delete_emp_record(self):
        for rec in self.emp_appraisal_line_ids:
            if rec.select:
                if self.state == 'draft':
                    rec.unlink()
                else:
                    raise Warning(_('Appraisal Are Genereated or \'Closed\' '
                                    'or \'Cancel\''))


class hr_employee_appraisal_line(models.Model):
    _name = 'hr.employee.appraisal.line'

    appraisal_id = fields.Many2one('appraisal.year.master',
                                   string='Appraisal Id')
    select = fields.Boolean('Select')
    emp_id = fields.Many2one('hr.employee', string='Employee Name')
    emp_no = fields.Integer(string='Employee No',
                            help="Employee ID")
    parent_id = fields.Many2one('hr.employee', string='Manager')
    upper_manager = fields.Many2one('hr.employee', string='Upper Manager')
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Title')
    employee_role = fields.Selection([('staff', 'Staff'),
                                      ('director', 'Director'),
                                      ('vp', 'Vice President'),
                                      ('ceo', 'CEO')], string='Employee Role')
    manager = fields.Boolean(string='Is a Manager')
    initial_employment_date = fields.Date('Hiring Date')
    state = fields.Selection([('pending', 'Pending'),
                              ('done', 'Done')], string='state')
