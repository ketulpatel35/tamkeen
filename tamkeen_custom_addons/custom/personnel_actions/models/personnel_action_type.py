from odoo import models, api, fields


class PersonnelActionType(models.Model):
    _name = 'personnel.action.type'
    _description = 'Personnel Action Type'

    name = fields.Char(string='Name') # Transfer
    code = fields.Char(string='Code')
    employee_list_to_display = fields.Selection([('occupy_position', 'Occupy '
                                                          'Position'),
                                       ('no_position', 'Not Occupy '
                                                       'Position')],
                                      string='Employee List to Display')
    vacant = fields.Boolean(string='Vacant')
    occupied = fields.Boolean(string='Occupied')
    un_occupied = fields.Boolean(string='Un-Occupied')
    obsolete = fields.Boolean(string='Obsolete')
    reason_action_ids = fields.One2many('reason.for.action',
                                        'personnel_action_type_id',
                                        string='Reason for Action')
    prior_position_required = fields.Boolean(string='Prior Position Required')
    new_position_required = fields.Boolean(string='New Position Required')
    company_id = fields.Many2one('res.company', string='Company')
    fill_occupied_by = fields.Boolean(string='Fill Occupied By')
    fill_main_position = fields.Boolean(string='Fill Main Position')
    erase_prior_main_position = fields.Boolean(string='Erase Prior Main '
                                                      'Position')
    erase_prior_occupied_by = fields.Boolean(string='Erase Prior Occupied '
                                                      'by')
    prior_grade_required = fields.Boolean(string='Prior Grade Required')
    new_grade_required = fields.Boolean(string='New Grade Required')
    create_new_compensation_profile = fields.Boolean(string='Create New '
                                                            'Compensation '
                                                            'Profile')
    update_compensation_profile = fields.Boolean(string='Update Compensation Profile')
    prior_position_editable = fields.Boolean(string='Prior Position Editable')
    applied_to_recruitment_cycle = \
        fields.Boolean(string="Applied to Recruitment Cycle")
    prior_basic_salary_required = fields.Boolean(string='Prior Basic Salary '
                                                        'Required')
    new_basic_salary_required = fields.Boolean(string='New Basic Salary '
                                                      'Required')
