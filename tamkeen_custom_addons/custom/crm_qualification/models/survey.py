# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Survey(models.Model):
    _name = _inherit = 'survey.survey'

    for_lead = fields.Boolean(string='Opportunity Qualification ?', help='''
        Check this if the current survey for opportunity qualification.
    ''')

    @api.multi
    def action_start_survey(self):
        """ Open the website page with the survey form """
        self.ensure_one()
        token = self.env.context.get('survey_token')
        trail = "/%s" % token if token else ""
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Survey",
            'target': 'self',
            'context': dict(self.env.context),
            'url': self.with_context(relative_url=True).public_url + trail
        }

class SurveyAnswer(models.Model):
    _name = _inherit = 'survey.user_input'

    def _supported_models(self):
        ''' 
            Return Supported Reference Models 
        '''
        return [
            'crm.lead',
        ]
    def _get_reference_models(self):
        sm = self._supported_models()
        return [
            (m.model, m.name) for m in self.env['ir.model']\
                .search([('model', 'in', sm)])
        ]

    reference_id = fields.Reference(
        string='Reference Document',
        selection=_get_reference_models)
