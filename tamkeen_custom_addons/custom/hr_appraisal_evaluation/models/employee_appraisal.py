# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import Warning, except_orm


class Employee_Appraisal(models.Model):
    _name = 'employee.appraisal'
    _description = 'Employee Appraisal'
    _rec_name = 'emp_id'
    _inherit = 'mail.thread'
    _order = 'id desc'

    @api.multi
    def write(self, vals):
        res = super(Employee_Appraisal, self).write(vals)
        if 'objective' in vals:
            if self.total_obj_weight != 100:
                raise except_orm('Warning', '\nTotal Weightage in objective '
                                            'should be equal to 100')
        return res

    @api.one
    @api.constrains('objective', 'career_discussion',
                    'individual_development_plans')
    def _check_validation(self):
        """
        check validation
        :return:
        """
        if not self._context.get('const_app', False):
            if self.emp_id.user_id and self.emp_id.user_id.id == \
                    self.env.user.id:
                if len(self.objective) < 3 or len(self.objective) > 6:
                    raise Warning(_('There must be minimum of 3 records or '
                                    'Maximum of records in Objectives Table'))
                if len(self.career_discussion) < 2:
                    raise Warning(_('Minimum of 2 records should be there in '
                                    'Career Discussion Table'))
                if len(self.individual_development_plans) == 0:
                    raise Warning(_('Minimum 1 record should be there in '
                                    'Individual Development Plan Table'))

    @api.model
    def _create_sequence(self):
        seq = self.env['ir.sequence'].next_by_code('employee.appraisal')
        return seq

    @api.depends('objective')
    def _compute_total_obj_weightage(self):
        """
        Compute total objective weightage
        :return:
        """
        weightage = 0.00
        for rec in self.objective:
            weightage += rec.weightage
        self.total_obj_weight = weightage

    @api.depends('behaviour_comp')
    def _compute_total_bvr_weightage(self):
        """
        Compute total behaviour weightage
        :return:
        """
        behaviour = 0.00
        for rec in self.behaviour_comp:
            behaviour += rec.weightage
        self.total_beh_weight = behaviour

    appraisal_sequence = fields.Char(string="Appraisal Sequence",
                                     default=_create_sequence)
    state = fields.Selection([('draft', 'Draft'),
                              ('sent_for_review', 'For Review'),
                              ('agreed_for_review', 'Agreed Reviewed'),
                              ('sent_for_hr_approval', 'HR Approval'),
                              ('cancel', 'Cancel'),
                              ('close', 'Closed')],
                             default='draft')
    emp_id = fields.Many2one('hr.employee', string="Employee Name",
                             help="Owner of the Appraisal Form")
    emo_no = fields.Integer(string='Employee No',
                            help="Employee ID")
    immediate_manager = fields.Many2one('hr.employee',
                                        string='Immediate Manager')
    to_upper_manager = fields.Many2one('hr.employee',
                                       string='Two Level Above Manager Name')
    appraisal_term = fields.Selection([('quarterly', 'Quarterly'),
                                       ('half_yearly', 'Half Yearly'),
                                       ('yearly', 'Yearly')],
                                      string='Appraisal Term')
    job_title = fields.Many2one('hr.job',
                                string='Job Title')
    date_of_joining = fields.Date(
        string='Date of Joining')

    current_date = fields.Date(string='Date', default=date.today())
    department_id = fields.Many2one('hr.department',
                                    string='Department')
    section = fields.Selection([('staff', 'Staff'),
                                ('director', 'Director'),
                                ('vp', 'Vice President'),
                                ('ceo', 'CEO')],
                               string='Section')

    period_from = fields.Date(string='Period From')
    period_to = fields.Date(string='Period To')
    objective = fields.One2many('objective.record',
                                'objective_id',
                                string='Objectives')
    agreed_date = fields.Date('Agreed Date')
    # achievement_date = fields.Selection([('0', 'Ongoing'),
    #                                      ('1', 'January'),
    #                                      ('2', 'Feburary'),
    #                                      ('3', 'March'),
    #                                      ('4', 'April'),
    #                                      ('5', 'May'),
    #                                      ('6', 'June'),
    #                                      ('7', 'July'),
    #                                      ('8', 'August'),
    #                                      ('9', 'September'),
    #                                      ('10', 'October'),
    #                                      ('11', 'November'),
    #                                      ('12', 'December')],
    #                                     string='Achievement Date')
    obj_total_weightage = \
        fields.Float(string='Total Weightage (%)')
    behaviour_comp = fields.One2many('behaviour.competences',
                                     'behaviour_comp_id',
                                     string='Behavioural Competencies')
    emo_technical = fields.Text(string='Technical')
    emo_behaviour = fields.Text(string='Behaviour')
    manager_technical = fields.Text(string='Technical')
    manager_behaviour = fields.Text(string='Behaviour')
    career_discussion = fields.One2many('career.discussion',
                                        'career_id',
                                        string='Career Discussion')
    individual_development_plans = \
        fields.One2many('individual.development.plan',
                        'emp_ref_id',
                        string='Individual Development Plan')

    emp_obj_avg_rating = fields.Float(compute='emp_calculate_ratings',
                                      store=True,
                                      string='Objective AVG Rating')
    emp_behaviour_comp_avg_rating = \
        fields.Float(compute='emp_calculate_ratings',
                     store=True,
                     string='behaviour Competences AVG Rating')
    emp_weightage_avg_rating = \
        fields.Float(compute='emp_calculate_ratings',
                     store=True,
                     string='Weightage AVG Rating')
    emp_final_rate = fields.Float(compute='emp_calculate_ratings',
                                  store=True,
                                  string='Final Rating')

    mng_obj_avg_rating = fields.Float(compute='mng_calculate_ratings',
                                      store=True,
                                      string='Objective AVG Rating')
    mng_behaviour_comp_avg_rating = \
        fields.Float(compute='mng_calculate_ratings',
                     store=True,
                     string='behaviour Competences AVG Rating')
    mng_weightage_avg_rating = \
        fields.Float(compute='mng_calculate_ratings',
                     store=True,
                     string='Weightage AVG Rating')
    mng_final_rate = fields.Float(string='Final Rating')
    mng_final_rate_after_calibration = \
        fields.Many2one('rating.master', string='Final Rating After '
                                                'Calibration')
    objective_weightage = \
        fields.Float('Objective Total Weightage (%)')
    behaviour_total_weightage = \
        fields.Float('Behaviour Total Weightage (%)')
    imdt_mgr_reviewed = fields.Boolean('Reviewed By Immediate Manager '
                                       'complete !')
    total_obj_weight = fields.Float('Total Objective (%)',
                                    compute='_compute_total_obj_weightage')
    total_beh_weight = fields.Float('Total Behaviour (%)',
                                    compute='_compute_total_bvr_weightage')
    agreed_status = fields.Selection([('mutual_agreed', 'Mutual Agreed'),
                                      ('mutual_agreed_with_exception',
                                       'Mutual Agreed With Exception'),
                                      ('not_agreed', 'Not Agreed')],
                                     default='mutual_agreed')
    exception_agreed = fields.Text('Exception')
    appraisal_year_id = fields.Many2one('appraisal.year.master',
                                        string='Appraisal Year')
    current_app_year_rec = fields.Boolean(
        related='appraisal_year_id.is_current_year')
    f_employee_no = \
        fields.Char(related='emp_id.f_employee_no', string='Employee ID')

    # @api.one
    # @api.constrains('mng_final_rate')
    # def validation_final_rating(self):
    #     if self.mng_final_rate \
    #             and self.mng_final_rate > 10 or self.mng_final_rate < 1:
    #         raise Warning(_('Final Rating should be between 1 to 10'))

    @api.multi
    @api.depends('objective', 'behaviour_comp')
    def emp_calculate_ratings(self):
        emp_obj_weightage = []
        emp_beh_rating = []
        avg_obj_weightage_rating_line = 0.0
        avg_beh_weightage_rating_line = 0.0
        rating_master = self.env['rating.master']

        for rec in self.objective:
            emp_rating = rec.self_rating
            if emp_rating:
                # rating_id = rating_master.search(
                #     [('name', '=', emp_rating.name),
                #      ('type', '=', 'employee')])
                rating_id = rating_master.search(
                    [('name', '=', emp_rating.name)])
                rec.obj_self_rating = rating_id.rating
                avg_obj_weightage_rating_line = (rec.obj_self_rating *
                                                 rec.weightage) / 100
                emp_obj_weightage.append(avg_obj_weightage_rating_line)

        if len(emp_obj_weightage) > 0:
            self.emp_obj_avg_rating = sum(emp_obj_weightage)

        for rec in self.behaviour_comp:
            beh_emp_rating = rec.emp_behaviour_self_rating
            if beh_emp_rating:
                # rating_id = rating_master.search(
                #     [('name', '=', beh_emp_rating.name),
                #      ('type', '=', 'employee')])
                rating_id = rating_master.search(
                    [('name', '=', beh_emp_rating.name)])
                rec.emp_beh_rating = rating_id.rating
                avg_beh_weightage_rating_line = (rec.emp_beh_rating *
                                                 rec.weightage) / 100
                emp_beh_rating.append(avg_beh_weightage_rating_line)

        if len(emp_beh_rating) > 0:
            self.emp_behaviour_comp_avg_rating = sum(emp_beh_rating)

        self.emp_weightage_avg_rating = \
            ((self.emp_obj_avg_rating * self.objective_weightage) / 100) + (
                (self.emp_behaviour_comp_avg_rating *
                 self.behaviour_total_weightage) / 100)

    @api.multi
    @api.depends('objective', 'behaviour_comp')
    def mng_calculate_ratings(self):
        mng_obj_rating = []
        mng_beh_rating = []
        avg_obj_weightage_rating_line = 0.0
        avg_beh_weightage_rating_line = 0.0
        rating_master = self.env['rating.master']

        for rec in self.objective:
            manager_rating = rec.manager_rating
            if manager_rating:
                # rating_id = rating_master.search(
                #     [('name', '=', manager_rating.name),
                #      ('type', '=', 'manager')])
                rating_id = rating_master.search(
                    [('name', '=', manager_rating.name)])
                rec.obj_manager_rating = rating_id.rating
                avg_obj_weightage_rating_line = (rec.obj_manager_rating *
                                                 rec.weightage) / 100
            mng_obj_rating.append(avg_obj_weightage_rating_line)
        if len(mng_obj_rating) > 0:
            self.mng_obj_avg_rating = (sum(mng_obj_rating) *
                                       self.objective_weightage) / 100

        for rec in self.behaviour_comp:
            beh_manager_rating = rec.manager_behaviour_rating
            if beh_manager_rating:
                # rating_id = rating_master.search(
                #     [('name', '=', beh_manager_rating.name),
                #      ('type', '=', 'manager')])
                rating_id = rating_master.search(
                    [('name', '=', beh_manager_rating.name)])
                rec.mng_beh_rating = rating_id.rating
                avg_beh_weightage_rating_line = (rec.mng_beh_rating *
                                                 rec.weightage) / 100
                mng_beh_rating.append(avg_beh_weightage_rating_line)
        if len(mng_beh_rating) > 0:
            self.mng_behaviour_comp_avg_rating = \
                (sum(mng_beh_rating) * self.behaviour_total_weightage) / 100

        self.mng_weightage_avg_rating = \
            ((self.mng_behaviour_comp_avg_rating *
              self.objective_weightage) / 100) + (
                (self.mng_obj_avg_rating * self.behaviour_total_weightage) /
                100)

    @api.one
    def sent_for_review(self):
        """
        Employee send own Apprisal for reviewed
        :return:
        """
        if len(self.objective) == 0:
            raise except_orm('Warning', '\nTotal Weightage in objective '
                                        'should be equal to 100')
        if not self.emp_id.user_id:
            raise Warning(_('Employee has not Related User.'))
        if self.emp_id.user_id.id != self.env.user.id:
            raise Warning(_('Employee can send only own Appraisal for Review'))
        self.write({'state': 'sent_for_review'})

    @api.multi
    def agreed_for_review(self):
        """
        immediate manager agreed after review.
        :return:
        """
        # send for notification
        template_rec = self.env.ref(
            'hr_appraisal_evaluation.notification_to_vp_email_template')
        template_rec.send_mail(self.id, force_send=False,
                               raise_exception=False, email_values=None)

        if not self.immediate_manager.user_id:
            raise Warning(_('Immediate Manager has not Related User.'))
        if self.immediate_manager.user_id.id != self.env.user.id:
            raise Warning(_('Employee %s Appraisal Review by Immediate '
                            'Manager %s Only') % (self.emp_id.name,
                                                  self.immediate_manager.name))
        if not self.imdt_mgr_reviewed:
            raise Warning(_('Please check Review Complete !'))

        self.write({'state': 'agreed_for_review'})

    @api.multi
    def sent_for_hr_approval(self):
        """
        send for hr approval
        :return:
        """
        # if not self.immediate_manager.user_id:
        #     raise Warning(_('Immediate Manager has not Related User.'))
        # if self.immediate_manager.user_id.id != self.env.user.id:
        #     raise Warning(_('Immediate Manager %s only can send for Hr'
        #                     ' Approval') % (self.immediate_manager.name))
        self.write({'state': 'sent_for_hr_approval'})

    @api.multi
    def set_to_draft(self):
        """
        set to draft and blank manager all detail
        :return:
        """
        for rec in self:

            if not self.immediate_manager.user_id:
                raise Warning(_('Immediate Manager has not Related User.'))
            if self.immediate_manager.user_id.id != self.env.user.id:
                raise Warning(_('Employee %s Appraisal Review by Immediate '
                                'Manager %s Only') %
                              (self.emp_id.name, self.immediate_manager.name))
            # manager rating should be blank from objective
            for obj_rec in rec.objective:
                obj_rec.write({
                    'manager_rating': False,
                    'manager_mid_year_date': False,
                    'manager_end_year_date': False,
                    'manager_comments': '',
                    'check_manager_comment': False,
                })
            for bhvr_rec in rec.behaviour_comp:
                bhvr_rec.write({
                    'manager_behaviour_rating': False,
                    'improvement_area': '',
                    'check_manager_evidence': False,
                    'manager_evidence': '',
                })

            rec.write({
                'agreed_date': False,
                'agreed_status': '',
                'exception_agreed': '',
                'manager_technical': '',
                'manager_behaviour': '',
                'state': 'draft',
            })

    @api.multi
    def close(self):
        self.write({'state': 'close'})

    @api.multi
    def get_manager_objective(self):
        """
        Employee see the list of manager objective
        :return:
        """
        ids = []
        if self.immediate_manager:
            if self.appraisal_year_id:
                query = """select id from employee_appraisal where
                emp_id = %s and appraisal_year_id = %s""" % (
                    self.immediate_manager.id,
                    self.appraisal_year_id.id)
                self._cr.execute(query)
                res = self._cr.fetchall()
                if res:
                    objective_rec = self.env['objective.record'].search([
                        ('objective_id', 'in', res[0])])
                    ids = objective_rec.ids
        return {
            'name': _('Manager Objective'),
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'objective.record',
            'view_id': self.env.ref(
                'hr_appraisal_evaluation.manager_objective_tree').id,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', ids)],
        }
