from odoo import models, fields


class HrDepartment(models.Model):
    _inherit = 'hr.department'


    level_indexing_id = fields.Many2one('level.indexing', string='Level '
                                                                 'Indexing')


class HrJob(models.Model):
    _inherit = 'hr.job'


    level_indexing_id = fields.Many2one('level.indexing', string='Level '
                                                                 'Indexing')


class HrJobTemplate(models.Model):
    _inherit = 'hr.job.template'


    level_indexing_id = fields.Many2one('level.indexing', string='Level '
                                                                 'Indexing')
