# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class Behaviour_Types(models.Model):
    _name = 'behaviour.types'
    _description = 'Behaviour Types'
    _rec_name = 'behaviour_name'

    behaviour_comp_type_id = fields.Many2one('behaviour.competences')
    behaviour_name = fields.Char(string='Behaviour Name')
    region = fields.Text(string='Region')
    defination = fields.Text(string='Definition')
    weightage = fields.Float(string="Weightage")
    expected_level = fields.Many2one('rating.master', string='Expected Level')

    @api.one
    @api.constrains('weightage')
    def behaviour_rating_validation(self):
        if self.weightage and self.weightage > 40 or self.weightage < 1:
            raise Warning(_('Rating should be between 1 to 40 and Overall '
                            'Weightage of Total Records in Behaviour Type '
                            'Master should be equal to 100'))


class Behaviour_Competences(models.Model):
    _name = 'behaviour.competences'
    _description = 'Behaviour Competences'
    _rec_name = 'name'

    @api.multi
    @api.depends('emp_behaviour_self_rating', 'manager_behaviour_rating')
    def get_ratings(self):
        rating_master = self.env['rating.master']
        for rec in self:
            rec.emp_beh_rating, rec.mng_beh_rating = 0.0, 0.0

            beh_emp_rating = rec.emp_behaviour_self_rating
            beh_manager_rating = rec.manager_behaviour_rating
            if beh_emp_rating:
                rating_id = rating_master.search(
                    [('name', '=', beh_emp_rating.name)])
                rec.emp_beh_rating = rating_id.rating

            if beh_manager_rating:
                rating_id = rating_master.search(
                    [('name', '=', beh_manager_rating.name)])
                rec.beh_manager_rating = rating_id.rating

    behaviour_comp_id = fields.Many2one('employee.appraisal')
    name = fields.Many2one('behaviour.types', string='Behaviour')
    region = fields.Text(string='Region')
    definaition = fields.Text('Definition')
    expected_level = fields.Many2one('rating.master',
                                     string='Expected Level')
    emp_beh_rating = fields.Float('Rating', compute='get_ratings',
                                  store=True)
    mng_beh_rating = fields.Float('Rating', compute='get_ratings',
                                  store=True)
    emp_behaviour_self_rating = fields.Many2one('rating.master',
                                                string='Self Rating')
    manager_behaviour_rating = fields.Many2one('rating.master',
                                               string='Manager Rating')
    improvement_area = fields.Text(string='Improvement Areas')
    weightage = fields.Float('Weightage')
    check_emp_evidence = \
        fields.Boolean('Your Evidence',
                       default=False)
    check_manager_evidence = \
        fields.Boolean('Your Evidence',
                       default=False)
    emp_evidence_text = fields.Text(string='Employee Evidence')
    manager_evidence = fields.Binary(string='Manager Evidence')
    emp_evidence = fields.Binary('Employee Evidence')
