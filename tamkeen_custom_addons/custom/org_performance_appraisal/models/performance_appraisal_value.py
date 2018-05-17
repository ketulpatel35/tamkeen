from odoo import fields, models, api, _
# from odoo.exceptions import Warning


class PerformanceAppraisalValue(models.Model):
    _name = 'pa.value'
    _order = 'sequence'
    _description = 'Appraisal Performance Value'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Display Sequence')
    description = fields.Text('Description')


class ValueAssessment(models.Model):
    _name = 'pa.value.assessment'
    _description = 'Value Assessment'

    name = fields.Char('Name')
    description = fields.Text('Description')
    manager_assessment = fields.Many2one('rating.scale', 'Manager Assessment')
    evaluation_value = fields.Float('Evaluation Value',
                                    related='manager_assessment.points')
    performance_appraisal_id = fields.Many2one(
        'performance.appraisal', 'Performance Appraisal')