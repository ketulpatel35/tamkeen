# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.exceptions import ValidationError
from datetime import date, datetime


class Objectives_Types(models.Model):
    _name = 'objective.types'
    _description = 'Objective Types'
    _rec_name = 'objective_name'

    objective_type_id = fields.Many2one('objective.record')
    objective_name = fields.Text(string='Objective')
    kpi_measurement = fields.Text(string='KPI Measurement')
    weightage = fields.Float(string='Weightage')
    department_id = fields.Many2one('hr.department', string='Department')
    expected_level = fields.Many2one('rating.master',
                                     string='Expected Level')
    obj_description = fields.Char(string="Description")

    @api.one
    @api.constrains('weightage')
    def objective_type_rating_vlidation(self):
        if self.weightage and self.weightage > 40 or self.weightage < 1:
            raise Warning(_('Rating should be between 1 to 40'))


class Objective_Records(models.Model):
    _name = 'objective.record'
    _description = 'Objective Records'
    _rec_name = 'objectives'

    objective_id = fields.Many2one('employee.appraisal')
    temp_objective = fields.Text('Objectives')
    objectives = \
        fields.Many2one('objective.types', string='Objective')

    kpi_measurement = fields.Many2many(
        'kpi.type',
        'objective_kpi_type_rel',
        'objective_id',
        'kpi_type_id')
    kpi_description = fields.Text(string="KPI Description")
    # department_id = fields.Many2one(related='objectives.department_id',
    #                                 string='Department', store=True)
    weightage = \
        fields.Float(related='objectives.weightage', string='Weightage',
                     store=True)
    expected_level = fields.Many2one('rating.master',
                                     string='Expected Level',
                                     related='objectives.expected_level',
                                     store=True)
    obj_self_rating = fields.Float(string='Rating', compute='get_ratings',
                                   store=True)
    obj_manager_rating = fields.Float(string='Rating', compute='get_ratings',
                                      store=True)
    self_rating = fields.Many2one('rating.master', string='Self Rating')
    manager_rating = fields.Many2one('rating.master', string='Manager Rating')
    emp_mid_year_date = fields.Many2one('rating.master', string='Mid Year '
                                                                'Self Rating')
    emp_end_year_date = fields.Many2one('rating.master',
                                        string='End Year Self Rating')
    manager_mid_year_date = fields.Many2one('rating.master',
                                            string='Mid Year Manager Rating')
    manager_end_year_date = fields.Many2one('rating.master',
                                            string='End Year Manager Rating')
    check_emp_comment = \
        fields.Boolean('Comment', default=False)
    check_manager_comment = \
        fields.Boolean('Your Comment', default=False)
    emp_comments = fields.Text(string='Employee Comments')
    manager_comments = fields.Text(string='Manager Comments')
    emp_evidence = fields.Binary('Employee Evidence')
    achievement_date = fields.Selection([('0', 'Ongoing'),
                                         ('1', 'January'),
                                         ('2', 'Feburary'),
                                         ('3', 'March'),
                                         ('4', 'April'),
                                         ('5', 'May'),
                                         ('6', 'June'),
                                         ('7', 'July'),
                                         ('8', 'August'),
                                         ('9', 'September'),
                                         ('10', 'October'),
                                         ('11', 'November'),
                                         ('12', 'December')],
                                        string='Achievement Date')

    @api.one
    @api.constrains('weightage')
    def objective_type_rating_vlidation(self):
        if self.weightage and self.weightage > 40 or self.weightage < 1:
            raise Warning(_('Objective Weightage should be in between 1 to '
                            '40'))

    @api.multi
    @api.depends('self_rating', 'manager_rating')
    def get_ratings(self):
        rating_master = self.env['rating.master']
        for rec in self:
            rec.obj_self_rating, rec.obj_manager_rating = 0.0, 0.0

            emp_rating = rec.self_rating
            manager_rating = rec.manager_rating

            # if emp_rating:
            #     rating_id = rating_master.search([
            # ('name', '=', emp_rating.name), ('type', '=', 'employee')])
            #     rec.obj_self_rating = rating_id.rating
            #
            # if manager_rating:
            #     rating_id = rating_master.search(
            #         [('name', '=', manager_rating.name),
            #          ('type', '=', 'manager')])
            #     rec.obj_manager_rating = rating_id.rating

            if emp_rating:
                rating_id = rating_master.search(
                    [('name', '=', emp_rating.name)])
                rec.obj_self_rating = rating_id.rating

            if manager_rating:
                rating_id = rating_master.search(
                    [('name', '=', manager_rating.name)])
                rec.obj_manager_rating = rating_id.rating


class KPIType(models.Model):
    _name = 'kpi.type'
    _description = 'KPI Types'

    name = fields.Char(string="Name")


class EmployeeObjectives(models.Model):
    _name = 'employee.objective'
    _inherit = 'mail.thread'
    _description = 'Employee Objective'
    _rec_name = 'employee_id'

    @api.depends('emp_obj_line_ids')
    def _compute_total_obj_weightage(self):
        """
        Compute total objective weightage
        :return:
        """
        weightage = 0.00
        for rec in self.emp_obj_line_ids:
            weightage += rec.weightage
        self.total_obj_weight = weightage

    @api.model
    def get_current_year(self):
        """
        return current year
        :return:
        """
        return date.today().year

    @api.model
    def get_expect_grad_years(self):
        year_list = []
        current_year = self.get_current_year()
        start_year = 1990
        end_year = current_year + 3
        for y in range(start_year, end_year):
            year = str(y)
            year_list.append((year, year))
        return year_list

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  default=lambda self: self.env['hr.employee']
                                  .search([('user_id', '=', self._uid)],
                                          limit=1) or False)

    immediate_manager_id = fields.Many2one('hr.employee',
                                           related='employee_id.parent_id',
                                           string='Immediate Manager')
    objective_year = fields.Selection(get_expect_grad_years,
                                      string="Year")
    objective_agreed = fields.Date(string="Objective Agreed")
    can_date = fields.Date(string='Date')
    remarks = fields.Char(string='Remarks')
    emp_obj_line_ids = fields.One2many('employee.objective.line',
                                       'emp_objective_id', string="Objective"
                                                                  "Lines")
    total_obj_weight = fields.Float('Total Objective (%)',
                                    compute='_compute_total_obj_weightage',
                                    store="True")
    agreed_status = fields.Selection([('mutual_agreed', 'Mutual Agreed'),
                                      ('mutual_agreed_with_exception',
                                       'Mutual Agreed With Exception'),
                                      ('not_agreed', 'Not Agreed')],
                                     default='mutual_agreed')
    state = fields.Selection([
        ('draft', 'Draft'), ('manager_approval', 'Manager Approval'),
        ('mutual_agreed', 'Mutual Agreed'), ('cancel', 'Cancel'),
    ], readonly=True, default='draft', copy=False, string="Status")

    @api.multi
    def submit_for_approval(self):
        for rec in self:
            line_count = 0
            objective_list = []
            emp_objective = self.env[
                'emp.objective.config.settings'].search([], limit=1)
            min_obj = float(emp_objective.min_obj)
            max_obj = float(emp_objective.max_obj)
            for obj_line in rec.emp_obj_line_ids:
                line_count += 1
                objective_list.append(obj_line.objective_id.id)
            if len(objective_list) != len(set(objective_list)):
                raise Warning(_('Lines contains duplicate objective'))
            if line_count > max_obj:
                raise Warning(_('Maximum Objective Per Year should not be '
                                'greater than :%s') % max_obj)
            if line_count < min_obj:
                raise Warning(_('Minimum Objective Per Year should not be '
                                'less than :%s') % min_obj)

            if self.total_obj_weight == 100:
                pass
            else:
                raise Warning(_('Objective Weightage should be 100 %'))

            if not self.immediate_manager_id.user_id:
                raise Warning(_('Immediate Manager has not Related User.'))
            rec.write({'state': 'manager_approval'})
            if rec.state == 'manager_approval':
                tmpl_rec = self.env.ref(
                    'hr_appraisal_evaluation.'
                    'notification_to_manager_email_template')
                tmpl_rec.send_mail(self.id, force_send=False,
                                   raise_exception=False, email_values=None)
        return True

    @api.multi
    def to_manager_approval(self):
        users_obj = self.env['res.users']
        for rec in self:
            if rec.employee_id.user_id.id:
                if rec.employee_id.manager:
                    if rec.immediate_manager_id.name == \
                            rec.employee_id.parent_id.name:
                        if rec.immediate_manager_id.user_id.id == self._uid:
                            rec.write({'state': 'mutual_agreed',
                                       'objective_agreed': datetime.today(

                                       ).date(), 'agreed_status':
                                           'mutual_agreed'})
                        else:
                            raise ValidationError(
                                _('Only immediate manager can approve'))
                else:
                    if users_obj.has_group(
                            'hr_appraisal_evaluation.'
                            'group_app_manager_approval'):
                        rec.write({'state': 'mutual_agreed',
                                  'objective_agreed': datetime.today().date(

                                  ), 'agreed_status': 'mutual_agreed'})
                    else:
                        raise ValidationError(_('Only manager can approve'))

    @api.multi
    def to_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})
        return True

    @api.multi
    def to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
        return True


class EmployeeObjectivesLine(models.Model):
    _name = 'employee.objective.line'
    _description = 'Employee Objective Line'

    def _get_line_numbers(self):
        line_num = 1
        if self.ids:
            first_line_rec = self.browse(self.ids[0])
            for line_rec in first_line_rec.emp_objective_id.emp_obj_line_ids:
                line_rec.number = line_num
                line_num += 1

    number = fields.Integer(compute='_get_line_numbers', string='Sr.No ',
                            readonly=False, default=False)

    objective_id = fields.Many2one('objective.types', string="Objective")
    obj_std_description = fields.Char(string="Objective standard"
                                      " Description")
    emp_obj_text = fields.Char(string="Employee Objective")
    weightage = fields.Float(string="Weightage")
    remarks = fields.Char(string="Remarks")
    emp_objective_id = fields.Many2one('employee.objective',
                                       string="Objective ")
    kpi_measurement_ids = fields.Many2many('kpi.type', 'emp_obj_kpi_type_rel',
                                           'objective_id', 'kpi_type_id')

    @api.onchange('objective_id')
    def onchange_objective_id(self):
        """
        onchange objective id
        :return:
        """
        for rec in self:
            if rec.objective_id:
                rec.obj_std_description = rec.objective_id.obj_description
                rec.emp_obj_text = ''
                rec.weightage = rec.objective_id.weightage

    @api.one
    @api.constrains('weightage')
    def objective_weightage_vlidation(self):
        emp_objective = \
            self.env['emp.objective.config.settings'].search([], limit=1)
        min_weightage = float(emp_objective.min_weightage)
        max_weightage = float(emp_objective.max_weightage)
        if self.weightage < min_weightage:
            raise Warning(_('Objective Weightage should be greater than '
                            ':%s') % min_weightage)
        if self.weightage > max_weightage:
            raise Warning(_('Objective Weightage should be less than :%s') %
                          max_weightage)
