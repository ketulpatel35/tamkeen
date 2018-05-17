# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import Warning
from hijri import Convert_Date


class HrApplicant(models.Model):
    _name = "hr.applicant"
    _inherit = ['hr.applicant']

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
        end_year = current_year + 5
        for y in range(start_year, end_year):
            year = str(y)
            year_list.append((year, year))
        return year_list

    @api.multi
    def get_expect_grad_month(self):
        months_list = [('1', 'January'), ('2', 'February'), ('3', 'March'),
                       ('4', 'April'), ('5', 'May'), ('6', 'Jun'),
                       ('7', 'July'), ('8', 'August'), ('9', 'September'),
                       ('10', 'October'), ('11', 'November'),
                       ('12', 'December')]
        return months_list

    gender = fields.Selection([('male', 'male'), ('female', 'female')],
                              'Gender')
    marital = fields.Selection([('single', 'Single'), ('married', 'Married'),
                                ('widower', 'Widower'),
                                ('divorced', 'Divorced')],
                               'Marital Status')
    country_id = fields.Many2one('res.country', 'Nationality')
    identification_type = fields.Selection([
        ('National_ID', 'National ID'), ('Passport_Number', 'Passport Number'),
        ('Iqama_Number', 'Iqama Number')], string='Identification Type')
    identification_number = fields.Char('Identification Number')
    university = fields.Char('University')
    uni_location = fields.Many2one('res.country', 'University Location')
    major = fields.Many2one('hr.applicant.major', string='Major')
    other_major = fields.Char('Other Major')
    minor = fields.Char('Minor')
    gpa = fields.Char('GPA')
    gpa_max = fields.Char('GPA Maximum')
    expect_grad_year = fields.Selection(get_expect_grad_years,
                                        string='Expected Graduation Year',
                                        index=True)
    expect_grad_month = fields.Selection(get_expect_grad_month,
                                         'Expected Graduation Month',
                                         index=True)
    question_1 = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                  string='Have you been contacted for career '
                                         'opportunities at Tamkeen before?')
    question_2 = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                  string='Do you have any relatives or family '
                                         'members working at Tamkeen?')
    relative_name = fields.Char('Relative Name')
    relative_degree = fields.Char('Relative Degree')
    relative_department = fields.Char('Relative Department')
    date_of_birth = fields.Date('Date of Birth')
    date_of_birth_hijri = fields.Char('Hijri Date of Birth')
    current_location = fields.Char('Current Location')
    reference_ids = fields.One2many('hr.applicant.references', 'applicant_id',
                                    'References')

    @api.onchange('date_of_birth')
    def onchange_date_of_birth(self):
        if self.date_of_birth:
            self.date_of_birth_hijri = Convert_Date(
                self.date_of_birth, 'english', 'islamic')

    @api.onchange('date_of_birth_hijri')
    def onchange_date_of_birth_hijri(self):
        if self.date_of_birth_hijri:
            self.date_of_birth = Convert_Date(
                self.date_of_birth_hijri, 'islamic', 'english')

    @api.model
    def _check_unique_applicant(self, identification_number, job_id,
                                identification_type):
        """
        :return:
        """
        hr_applicant_obj = self.env['hr.applicant']
        if identification_number and identification_type and job_id:
            exist_applicant = hr_applicant_obj.search([
                ('identification_number', '=', identification_number),
                ('identification_type', '=', identification_type),
                ('job_id', '=', job_id)])
            if exist_applicant:
                return True
            else:
                return False

    @api.model
    def _get_job_applicant_stage(self):
        """
        :return:
        """
        stage_rec = self.env['hr.recruitment.stage'].search([
            ('name', '=', 'Job Application')], limit=1)
        if stage_rec:
            return stage_rec.id
        return False

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        if vals and 'identification_number' in vals and 'job_id' in vals \
                and 'identification_type' in vals:
            app_validation = self._check_unique_applicant(
                vals['identification_number'], vals['job_id'],
                vals['identification_type'])
            if app_validation:
                raise Warning(_('Warning !\n'
                                'You have already Applied for this job. !'))
        # if not vals['stage_id']:
        #     if self._default_stage_id():
        #         vals['stage_id'] = self._default_stage_id()
        #     else:
        #         vals['stage_id'] = self._get_job_applicant_stage()
        return super(HrApplicant, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        :param vals:
        :return:
        """
        for rec in self:
            # import ipdb;ipdb.set_trace()
            if vals and 'identification_number' in vals \
                    or 'identification_type' in vals or 'job_id' in vals:
                identification_number = rec.identification_number
                if 'identification_number' in vals:
                    identification_number = vals['identification_number']
                identification_type = rec.identification_type
                if 'identification_type' in vals:
                    identification_type = vals['identification_type']
                job_id = False
                if rec.job_id:
                    job_id = rec.job_id.id
                if 'job_id' in vals:
                    job_id = vals['job_id']
                if identification_number and job_id and identification_type:
                    app_validation = rec._check_unique_applicant(
                        identification_number, job_id, identification_type)
                    if app_validation:
                        raise Warning(_('Warning !\n You have already '
                                        'Applied for this job. !'))
        return super(HrApplicant, self).write(vals)


class HrApplicantReferences(models.Model):
    _name = 'hr.applicant.references'

    applicant_id = fields.Many2one('hr.applicant', 'Applicant',
                                   required=True, readonly=True,
                                   ondelete="cascade")
    reference = fields.Selection([('manager', 'Manager'),
                                  ('colleague', 'Colleague')],
                                 string='Reference', index=True)
    specification = fields.Selection([('previous', 'Previous'),
                                      ('current', 'Current')],
                                     string='Specification', index=True)
    name = fields.Char('Name')
    job_title = fields.Char('Job Title')
    company = fields.Char('Company')
    mobile = fields.Char('Mobile Number')
    email = fields.Char('Email', size=128)
    date = fields.Date('Contact Date')
    feedback = fields.Text('Feedback')


class HrApplicantMajor(models.Model):
    _name = 'hr.applicant.major'

    name = fields.Char(string='Name')

# class HrApplicantReferences_type(models.Model):
#     _name= 'hr.applicant.references.type'
#
#     name = fields.Char('Name', size=64, required=True)
