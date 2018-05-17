from odoo import models, api, fields, _
from odoo.exceptions import Warning


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'Position'

    # @api.multi
    # def _get_head_own_org_unit(self):
    #     for rec in self:
    #         if rec.department_id and rec.department_id.holder_position_id \
    #                 and rec.department_id.holder_position_id.id == rec.id:
    #             rec.head_own_org_unit = True
    #         else:
    #             rec.head_own_org_unit = False
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        args = args or []
        records = self.search(
            ['|', ('code', operator, name), ('name', operator, name)] + args,
            limit=limit)
        return records.name_get()

    @api.multi
    def name_get(self):
        """
        name should display with code
        :return:
        """
        res = []
        for record in self:
            code = record.code or ''
            name = record.name or ''
            display_name = '[ ' + code + ' ] ' + name
            res.append((record.id, display_name.title()))
        return res

    job_template_id = fields.Many2one('hr.job.template', string='Job Template')
    employee_id = fields.Many2one('hr.employee',
                                               string='Occupied By')
    name = fields.Char(string='Name', required=True, index=True,
                      translate=True)
    department_id = fields.Many2one('hr.department', string='Organization '
                                                            'Unit')
    vacant = fields.Boolean(string='Vacant')
    obsolete = fields.Boolean(string='Obsolete')
    code = fields.Char(string='Code', help='It will be unique per position')
    # org_unit_id = fields.Many2one('hr.department', string='Organization Unit')
    parent_id = fields.Many2one('hr.job', string='Reporting To')
    reporting_to_employee_id = fields.Many2one('hr.employee',
                                               string='Reporting To '
                                                      'Employee',
                                               related='parent_id.employee_id')
    child_ids = fields.One2many('hr.job', 'parent_id', string='Position '
                                                              'Hierarchy')
    head_own_org_unit = fields.Boolean(string='Head Of Own Organization Unit')
    schedule_template_id = fields.Many2one('resource.calendar',
                                           string='Working Schedule Template')
    department_staff = fields.Selection([('department', 'Department'),
                                         ('staff', 'Staff')],
                                        string='Department/Staff')
    state = fields.Selection([('planned', 'Planned'), ('submitted',
                                                       'Submitted'),
                              ('rejected', 'Rejected'), ('approved',
                                                         'Approved'),
                              ('active', 'Active'), ('recruit', 'Recruitment in Progress'),
        ('open', 'Not Recruiting')], string='Status', default='planned',
                             track_visibility='onchange', copy=False,
                             readonly=True, required=True)
    short_name = fields.Char(string='Short Name', traslate=True)
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    employee_group_id = fields.Many2one('hr.employee.group',
                                        string='Employee Group')
    employee_sub_group_id = fields.Many2one('hr.employee.group',
                                            string='Employee Sub Group')
    personnel_area_id = fields.Many2one('personnel.area',
                                        string='Personnel Area')
    personnel_sub_area_id = fields.Many2one('personnel.area',
                                            string='Personnel Sub Area')
    duties = fields.Text(string='Duties')
    # payroll_period_schedule_id = fields.Many2one(
    #     'hr.payroll.period.schedule', string='Payroll Period Schedule')
    # policy_group_id = fields.Many2one('hr.policy.group', string='Policy Group')

    @api.model
    def _auto_init(self):
        res = super(HrJob, self)._auto_init()
        # Remove constrains for vat, nrc on "commercial entities" because is not mandatory by legislation
        # Even that VAT numbers are unique, the NRC field is not unique, and there are certain entities that
        # doesn't have a NRC number plus the formatting was changed few times, so we cannot have a base rule for
        # checking if available and emmited by the Ministry of Finance, only online on their website.

        self.env.cr.execute("""
                alter table hr_job drop CONSTRAINT if exists
                hr_job_name_company_uniq;
            """)
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(HrJob, self).default_get(fields_list)
        if self._context:
            if self._context.get('active_id') and self._context.get(
                    'active_model') == 'hr.department':
                res.update({'department_id': self._context.get(
                    'active_id')})
            if self._context.get('active_id') and self._context.get(
                    'active_model') == 'hr.job.template':
                res.update({'job_template_id': self._context.get(
                    'active_id')})
        return res

    @api.multi
    def action_head_of_own_org_unit(self):
        for rec in self:
            if rec.head_own_org_unit:
                rec.department_id.write({'holder_position_id': False})
                rec.write({'head_own_org_unit': False})
            else:
                if rec.department_id and rec.department_id.holder_position_id:
                    raise Warning(_('You are not allowed to do this change '
                                    'becauase there is another holder position '
                                    'for this organiation unit.'))
                else:
                    rec.department_id.write({'holder_position_id': rec.id})
                    rec.write({'head_own_org_unit': True})

    @api.onchange('job_template_id')
    def onchange_job_template_id(self):
        if self.job_template_id:
            self.employee_group_id = self.job_template_id.employee_group_id
            self.employee_sub_group_id = self.job_template_id.employee_sub_group_id
            self.department_staff = self.job_template_id.department_staff
            self.description = self.job_template_id.description
            self.requirements = self.job_template_id.requirements
            self.duties = self.job_template_id.duties

    @api.onchange('department_id')
    def onchange_department_id(self):
        if self.department_id:
            self.schedule_template_id = \
                self.department_id.schedule_template_id

    _sql_constraints = [
        ('code_uniq', 'unique(code, company_id)',
         'Code should be unique per position!')]

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        if vals:
            seq = self.env['ir.sequence'].next_by_code('hr.job')
            vals.update({'code': seq})
        res = super(HrJob, self).create(vals)
        return res

    # overwite the default method
    # @api.multi
    def _compute_application_count(self):
        for rec in self:
            read_group_result = self.env['hr.applicant'].read_group([(
                'job_id', '=', rec.id)], ['job_id'], ['job_id'])
            result = dict((data['job_id'][0], data['job_id_count']) for data in
                          read_group_result)
            rec.application_count = result.get(rec.id, 0)

    @api.depends('no_of_recruitment', 'employee_ids.job_id',
                 'employee_ids.active')
    def _compute_employees(self):
        for job in self:
            job.no_of_employee = 0
            job.expected_employees = 0

    @api.multi
    def submit_for_approval(self):
        for rec in self:
            rec.write({'state': 'submitted'})

    @api.multi
    def button_approved(self):
        for rec in self:
            rec.write({'state': 'approved'})

    @api.multi
    def button_rejected(self):
        for rec in self:
            rec.write({'state': 'rejected'})

    @api.multi
    def button_active(self):
        for rec in self:
            rec.write({'state': 'active'})