# -*- coding: utf-8 -*-
##############################################################################
from odoo import http, _
import werkzeug.utils
from odoo.http import request
import simplejson
from odoo.addons.web.controllers.main import module_boot, login_and_redirect
import json

class organization_chart(http.Controller):
    @http.route(['/tree_chart/<string:tree_title>/<int:tree_id>'], type='http', auth="user", website=True)
    def draw_chart(self, tree_title, tree_id, **kwargs):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        if not session.uid:
            return werkzeug.utils.redirect(
                '/web/login')
        tree_title = tree_title.replace("_"," ").title()
        context = {
            'tree_id': tree_id,
            'tree_title': tree_title,
            'username': request.env.user.name,
            'session_info': json.dumps(request.env['ir.http'].session_info())
        }
        return request.render('organization_chart.organization_chart', qcontext=context)