from odoo import fields, models, api, _
# from odoo.exceptions import Warning


class PersonalCompetency(models.Model):
    _name = 'personal.competency'
    _order = 'sequence'
    _description = 'Personal Competency'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Display Sequence')
    description = fields.Text('Description')


class PersonalCompetencyAssessment(models.Model):
    _name = 'personal.competency.assessment'
    _description = 'Personal Competency Assessment'

    name = fields.Char('Name')
    description = fields.Text('Description')
    manager_assessment = fields.Many2one('rating.scale', 'Manager Assessment')
    evaluation_value = fields.Float('Evaluation Value',
                                    related='manager_assessment.points')
    performance_appraisal_id = fields.Many2one(
        'performance.appraisal', 'Performance Appraisal')