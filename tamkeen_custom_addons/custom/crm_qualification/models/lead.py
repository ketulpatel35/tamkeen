# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _name = _inherit = 'crm.lead'

    def _default_survey_id(self):
        return self.env['survey.survey']\
            .search([
                ('for_lead', '=', True),
            ], limit=1)
    
    @api.depends('qualification_result_id.user_input_line_ids.quizz_mark')
    def _compute_quizz_score(self):
        for r in self:
            r.qualification_score = sum(
                    r.qualification_result_id.user_input_line_ids.mapped('quizz_mark'))

    qualification_status = fields.Selection([
        ('review', 'Under Review'),
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Qualification Status', default='review')

    qualification_survey_id = fields.Many2one(
        'survey.survey', string='Qualification Survey', default=lambda self: self._default_survey_id())
    qualification_result_id = fields.Many2one('survey.user_input', string='Qualification Result')
    qualification_score = fields.Float(
        string='Qualification Score', compute='_compute_quizz_score', store=True)
    qualification_result_state = fields.Selection([
        ('new', 'Not started yet'),
        ('skip', 'Partially completed'),
        ('done', 'Completed'),
    ], string='Qualification Result State',
    related='qualification_result_id.state', store=True)

    @api.multi
    def action_qualification_survey_results(self):
        self.ensure_one()
        if not len(self.qualification_result_id):
            return
        return {
            'type': 'ir.actions.act_url',
            'name': "View Answers",
            'target': 'self',
            'url': '%s/%s' % (self.qualification_result_id.print_url, self.qualification_result_id.token)
        }

    @api.multi
    def action_start_qualification_survey(self):
        for r in self:
            if len(r.qualification_survey_id) < 1:
                raise exceptions.Warning(
                    _('Qualification Survey is not configured, please contact system administrator !')
                )
            result_id = len(r.qualification_result_id) and r.qualification_result_id.token or False
            if not result_id:
                srid = self.env['survey.user_input'].create({
                    'survey_id': r.qualification_survey_id.id,
                    'reference_id': u'crm.lead,{}'.format(r.id),
                    'type': 'manually',
                    'partner_id': self.env.user.partner_id.id,
                })
                r.write({
                    'qualification_result_id': srid.id,
                })
                result_id = srid.token
            return r.qualification_survey_id.with_context( survey_token=result_id).action_start_survey()
        return
