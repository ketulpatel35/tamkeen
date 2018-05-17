# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class rating_master(models.Model):
    _name = 'rating.master'
    _description = 'Type and Rating'

    rating_category_id = fields.Many2one('employee.appraisal')
    name = fields.Char('Name')
    rating = fields.Float('Ratings (0-10)')
    type = fields.Selection([('rating', 'Rating'),
                             ('objective', 'Objective'),
                             ('behaviour', 'Behaviour'),
                             ('development', 'Development Objectives'),
                             ('justification', 'Justification')],
                            default='rating')

    @api.one
    @api.constrains('rating')
    def rating_master_validation(self):
        if self.rating and self.rating > 10 or self.rating < 1:
            raise Warning(_('Rating should be between 1 to 10'))


class Career_Discussion(models.Model):
    _name = 'career.discussion'
    _description = 'Career Discription'
    _rec_name = 'career_discusion'

    career_id = fields.Many2one('employee.appraisal')
    career_discusion = fields.Selection([('1', 'Short term (18 to 24 Months)'),
                                         ('2', 'Long Term (Longer than 24 '
                                               'Months)')],
                                        string='Career Term')
    description = fields.Text(string='Description')
    requirements = fields.Text(string='Requirement and Time Frame')


class Individual_Development_Plan(models.Model):
    _name = 'individual.development.plan'
    _description = 'Individual Develoment Plan'

    emp_ref_id = fields.Many2one('employee.appraisal')
    development_obj = \
        fields.Char('Development Objectives')
    Justification = \
        fields.Many2one('rating.master', string='Justification')
    detail_description = \
        fields.Text('Detailed Descriptions')
    development_options = fields.Many2one('rating.master',
                                          string='Development Options')
    intervention = fields.Text('Interventions')
    # success_measurre = fields.Float('Success Measures')
    target_completion_date = fields.Date('Completion Date')
    remark = fields.Text('Remarks')

    # @api.one
    # @api.constrains('success_measurre')
    # def idp_rating_validation(self):
    #     if self.success_measurre and self.success_measurre > 10 \
    #             or self.success_measurre < 1:
    #         raise Warning(_('Individual Developemtn Plan Rating '
    #                         'should be between 1 to 10'))


class Requirement_Category(models.Model):
    _name = 'requirement.category'
    _description = 'Category and Their Weightage'

    category_id = fields.Many2one('employee.appraisal')
    category_type = fields.Selection([('1', 'Objective'),
                                      ('2', 'Behaviour')],
                                     string='Category Name')
    Weightage = fields.Float('Total Weightage (0-100)%')
    type = fields.Selection([('employee', 'Employee'),
                             ('manager', 'Manager')])

    @api.one
    @api.constrains('Weightage')
    def req_cat_rrating_validation(self):
        if self.Weightage and self.Weightage > 100 \
                or self.Weightage < 1:
            raise Warning(_('Category Rating should be between 1 to 100'))
