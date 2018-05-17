# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from datetime import datetime
from math import ceil

from odoo import fields, http, SUPERUSER_ID
from odoo.http import request
from odoo.tools import ustr
from odoo.addons.survey.controllers import main

_logger = logging.getLogger(__name__)


class WebsiteSurvey(main.WebsiteSurvey):
    @http.route(['/survey/start/<model("survey.survey"):survey>',
                 '/survey/start/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True)
    def start_survey(self, survey, token=None, **post):
        args = request.httprequest.args
        lid = args.get('lead_id', False)
        if lid:
            try:
                lid = int(lid)
                request.env['crm.lead'].sudo().browse(lid)
            except Exception as e:
                lid = False
        UserInput = request.env['survey.user_input']

        # Test mode
        if token and token == "phantom":
            _logger.info("[survey] Phantom mode")
            user_input = UserInput.with_context(lead_id=lid).create(
                {'survey_id': survey.id, 'test_entry': True})
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.render('survey.survey_init', data)
        # END Test mode

        # Controls if the survey can be displayed
        errpage = self._check_bad_cases(survey, token=token)
        if errpage:
            return errpage

        # Manual surveying
        if not token:
            vals = {'survey_id': survey.id}
            if request.website.user_id != request.env.user:
                vals['partner_id'] = request.env.user.partner_id.id
            user_input = UserInput.with_context(lead_id=lid).create(vals)
        else:
            user_input = UserInput.sudo().search(
                [('token', '=', token)], limit=1)
            if not user_input:
                return request.render("website.403")

        # Do not open expired survey
        errpage = self._check_deadline(user_input)
        if errpage:
            return errpage

        # Select the right page
        if user_input.state == 'new':  # Intro page
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.render('survey.survey_init', data)
        else:
            return request.redirect('/survey/fill/%s/%s' % (survey.id, user_input.token))
