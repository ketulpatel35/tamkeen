from odoo import models, api, fields, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning

class PersonnelActions(models.Model):
    _name = 'personnel.actions'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Reference', track_visibility='onchange')
    action_type_id = fields.Many2one('personnel.action.type',
                                     string='Action', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee Company ID',
                                      store=True)
    prior_position_id = fields.Many2one('hr.job', string='Prior Position')
    new_position_id = fields.Many2one('hr.job', string='New Position')
    acting_percentage = fields.Float(string='Acting Percentage')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    reason_action_id = fields.Many2one('reason.for.action', string='Reason '
                                                                   'For '
                                                                   'Action')
    prior_position_required = fields.Boolean(string='Prior Position '
                                                    'Required',
                                             related='action_type_id.prior_position_required', store=True)
    prior_position_editable = fields.Boolean(string='Prior Position Editable'
                                                    'Required',
                                             related='action_type_id.prior_position_editable', store=True)
    new_position_required = fields.Boolean(string='New Position Required',
                                           related='action_type_id.new_position_required', store=True)
    prior_org_unit = fields.Many2one('hr.department',
                                     related='prior_position_id.department_id',
                                     string='Prior Organization Unit',
                                     track_visibility='onchange')
    new_org_unit = fields.Many2one('hr.department', string='New '
                                                             'Organization '
                                                             'Unit',
                                   related='new_position_id.department_id',
                                   track_visibility='onchange')
    prior_grade_level_id = fields.Many2one('grade.level',
                                     string='Prior '
                                            'Grade '
                                            'Level',
                                           track_visibility='onchange')
    new_grade_level_id = fields.Many2one('grade.level',
                                           string='New '
                                                  'Grade '
                                                  'Level',
                                         track_visibility='onchange')
    prior_grade_required = fields.Boolean(
        string='Prior Grade Level Required',
        related='action_type_id.prior_grade_required', store=True)
    new_grade_required = fields.Boolean(
        string='New Grade Level Required',
        related='action_type_id.new_grade_required',
        store=True)

    prior_basic_salary_required = fields.Boolean(
        string='Prior Basic Salary Required',
        related='action_type_id.prior_basic_salary_required',
        store=True)
    new_basic_salary_required = fields.Boolean(
        string='New Basic Salary Required',
        related='action_type_id.new_basic_salary_required',
        store=True)
    prior_basic_salary = fields.Float(string='Prior Basic Salary',
                                      related='contract_id.wage', store=True)
    new_basic_salary = fields.Float(string='New Basic Salary')
    contract_id = fields.Many2one('hr.contract', string='Prior Compensation '
                                                        'Profile')
    state = fields.Selection([('planned', 'Planned'),
                              ('submitted', 'Submitted'),
                              ('rejected', 'Rejected'),
                              ('approved', 'Approved'),
                              ('active', 'Active'), ('locked', 'Locked')],
                             string='Status',
                             default='planned', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company')

    @api.onchange('employee_id')
    def get_prior_position(self):
        self.prior_position_id = False
        if self.employee_id and \
                self.employee_id.job_id:
            self.prior_position_id = self.employee_id.job_id.id
            self.new_grade_level_id = self.employee_id.job_id.grade_level_id.id
        if self.employee_id and self.employee_id.contract_id:
            self.contract_id = self.employee_id.contract_id.id
            if self.employee_id.contract_id.grade_level:
                self.prior_grade_level_id = self.employee_id.contract_id.grade_level.id


    @api.onchange('new_position_id')
    def onchange_new_position_id(self):
        if self.new_position_id:
            self.new_grade_level_id = self.new_position_id.grade_level_id.id

    @api.model
    def default_get(self, fields_list):
        res = super(PersonnelActions, self).default_get(fields_list)
        today = date.today()
        to_date = today + relativedelta(year=9999, day=31, month=12)
        res.update({'date_to': str(to_date)})
        return res

    @api.model
    def create(self, vals):
        reference = self.env['ir.sequence'].next_by_code(
            'personnel.actions') or ''
        vals.update({'name': reference})
        # if vals.get('employee_id'):
        #     employee_rec = self.env['hr.employee'].browse(vals.get(
        #         'employee_id'))
        #     if employee_rec and employee_rec.job_id:
        #         vals.update({'prior_position_id': employee_rec.job_id.id})
        #     if employee_rec.contract_id and \
        #             employee_rec.contract_id.grade_level:
        #         vals.update({'prior_grade_level_id':
        #                          employee_rec.contract_id.grade_level.id,
        #                      'contract_id': employee_rec.contract_id.id})
        return super(PersonnelActions, self).create(vals)

    # @api.multi
    # def write(self, vals):
    #     for rec in self:
    #         employee_id = vals.get('employee_id') or rec.employee_id.id
    #         current_state = vals.get('state') or rec.state
    #         if employee_id and current_state in ('planned'):
    #             employee_rec = self.env['hr.employee'].browse(employee_id)
    #             if employee_rec and employee_rec.job_id:
    #                 vals.update({'prior_position_id': employee_rec.job_id.id})
    #             if employee_rec.contract_id and \
    #                     employee_rec.contract_id.grade_level:
    #                 vals.update({'prior_grade_level_id':
    #                                  employee_rec.contract_id.grade_level.id, 'contract_id': employee_rec.contract_id.id})
    #     return super(PersonnelActions, self).write(vals)

    @api.multi
    def copy(self, default=None):
        # if not self._check_group(
        #         'service_management.group_service_on_behalf_approval_srvs'
        # ):
        for rec in self:
            if rec.employee_id.user_id.id != self._uid:
                raise Warning(_(
                    "You don't have the permissions to make such changes."
                ))
        return super(PersonnelActions, self).copy(default=default)

    @api.multi
    def unlink(self):
        for record in self:
            if record.state not in ['planned']:
                raise ValidationError(_('You can only delete '
                                        'the requests in planned state.'))
        return super(PersonnelActions, self).unlink()

    @api.onchange('action_type_id')
    def onchange_action_type_id(self):
        result = {}
        employee_domain = []
        position_domain = []
        add_or = []
        if self.action_type_id:
            self.reason_action_id = False
            self.employee_id = False
            self.prior_position_id = False
            self.new_position_id = False
            self.new_grade_level_id = False
            self.prior_grade_level_id = False
            if self.action_type_id.employee_list_to_display == 'occupy_position':
                employee_domain.append(('job_id', '!=', False))
            elif self.action_type_id.employee_list_to_display == 'no_position':
                employee_domain.append(('job_id', '=', False))
            if self.action_type_id.vacant:
                position_domain.append(('vacant', '=', True))
            if self.action_type_id.occupied:
                position_domain.append(('employee_id', '!=', False))
            if self.action_type_id.un_occupied:
                position_domain.append(('employee_id', '=', False))
            if self.action_type_id.obsolete:
                position_domain.append(('obsolete', '=', True))
            position_domain_length = len(position_domain) - 1
            for position in range(position_domain_length):
                add_or += ['|']
            new_domain = add_or + position_domain
            result['domain'] = {
                'employee_id': employee_domain, 'new_position_id': new_domain}
        return result

    def _check_occupied_by(self, position):
        if position.employee_id:
            raise Warning(_('The select position already occupied by '
                            '%s.\n\n Please  take necessary action on '
                            'that employee to '
                            'continue.') % position.employee_id.name)

    @api.multi
    def submit_for_approval(self):
        for rec in self:
            if rec.action_type_id and \
                    rec.action_type_id.create_new_compensation_profile:
                rec._get_info_position()
            rec._check_occupied_by(rec.new_position_id)
            rec.write({'state': 'submitted'})

    @api.multi
    def button_approved(self):
        for rec in self:
            rec.write({'state': 'approved'})

    @api.multi
    def button_rejected(self):
        for rec in self:
            rec.write({'state': 'rejected'})

    def _get_info_position(self):
        warning_message = ''
        pps_id, policy_group_id, struct_id, schedule_template_id, \
        department_id = False, False, False, False, False
        wage = self.new_basic_salary
        if self.new_position_id:
            struct_id = self.new_position_id.struct_id.id if \
                self.new_position_id.struct_id else False
            # pps_id = self.new_position_id.payroll_period_schedule_id.id if \
            #     self.new_position_id.payroll_period_schedule_id else False
            # policy_group_id = self.new_position_id.policy_group_id.id if \
            #     self.new_position_id.policy_group_id else False
            schedule_template_id = \
                self.new_position_id.schedule_template_id.id if \
                    self.new_position_id.schedule_template_id else False
            department_id = self.new_position_id.department_id.id if \
                self.new_position_id.department_id else False
            # wage = self.new_grade_level_id.wage if self.new_grade_level_id \
            #     else 0.0
            if not struct_id:
                warning_message = 'Salary Structure, '
            # if not pps_id:
            #     warning_message += 'Payroll Period, '
            # if not policy_group_id:
            #     warning_message += 'Policy Group, '
            if not schedule_template_id:
                warning_message += 'Working Schedule Template, '
            if not department_id:
                warning_message += 'Department, '
            if warning_message:
                raise Warning(_('The Contract is not created because of the '
                                'some missing information. Kindly check %s '
                                'information in '
                                'position.')%warning_message)
        # return struct_id, pps_id, policy_group_id, schedule_template_id,\
        #        department_id, wage
        return struct_id, schedule_template_id, \
               department_id, wage

    def compensation_profile_value(self):
        vals = {}
        # struct_id, pps_id, policy_group_id, schedule_template_id, \
        # department_id, wage = self._get_info_position()
        struct_id, schedule_template_id, \
        department_id, wage = self._get_info_position()
        if self.new_position_id:
            vals.update({
                'job_id': self.new_position_id.id,
                'department_id': department_id,
            })
        if self.new_grade_level_id:
            vals.update({
                'grade_level': self.new_grade_level_id.id if
                     self.action_type_id.new_grade_required and
                     self.new_grade_level_id else False
            })
        if self.new_basic_salary:
            vals.update({
                'wage': wage,
            })
        # vals.update({'employee_id': self.employee_id.id,
        #              'job_id': self.new_position_id.id,
        #              'date_start': self.date_from,
        #              'date_end': self.date_to,
        #              'wage': wage,
        #              'department_id': department_id,
        #              'struct_id': struct_id,
        #              # 'pps_id': pps_id,
        #              # 'policy_group_id': policy_group_id,
        #              'working_hours': schedule_template_id,
        #              'grade_level': self.new_grade_level_id.id if
        #              self.action_type_id.new_grade_required and
        #              self.new_grade_level_id else False})
        return vals

    def create_compensation_profile(self):
        contract_obj = self.env['hr.contract']
        vals = self.compensation_profile_value()
        contract_rec = contract_obj.create(vals)
        self.write({'contract_id': contract_rec.id})

    def update_compensation_profile(self):
        if self.contract_id:
            vals = self.compensation_profile_value()
            self.contract_id.write(vals)
        else:
            raise Warning(_('"Kindly, To proceed with this action, '
                            'that employee should have a compensation '
                            'profile." %s')%self.employee_id.name)

    @api.multi
    def button_active(self):
        for rec in self:
            #for Employee
            if rec.action_type_id and rec.action_type_id.fill_main_position:
                rec.employee_id.write({'job_id':
                                           rec.new_position_id.id})
            #for Position
            if rec.action_type_id and \
                    rec.action_type_id.erase_prior_occupied_by:
                rec.prior_position_id.write({'employee_id': False})
            if rec.action_type_id and rec.action_type_id.fill_occupied_by:
                rec.new_position_id.write({'employee_id':
                                           rec.employee_id.id})
            if rec.action_type_id and rec.action_type_id.new_grade_required \
                    and rec.contract_id:
                rec.contract_id.write({'grade_level':
                                           rec.new_grade_level_id.id})
            if rec.action_type_id and \
                    rec.action_type_id.create_new_compensation_profile:
                rec.create_compensation_profile()
            if rec.action_type_id and \
                    rec.action_type_id.update_compensation_profile:
                rec.update_compensation_profile()
            rec.write({'state': 'active'})
