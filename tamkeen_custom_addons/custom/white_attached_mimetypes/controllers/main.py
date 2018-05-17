# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Binary
import json
from odoo.tools.translate import _
# import base64


class InheritBinary(Binary):

    @http.route('/web/binary/upload_attachment', type='http', auth="user")
    def upload_attachment(self, callback, model, id, ufile):
        ir_attachment_obj = request.env['ir.attachment']
        out = """<script language="javascript" type="text/javascript">
                    var win = window.top.window;
                    win.jQuery(win).trigger(%s, %s);
                </script>"""
        # attachment_allow = ir_attachment_obj.is_allowed_attachment(
        #     base64.encodestring(ufile.read()))
        attachment_allow = ir_attachment_obj.is_allowed_attachment_check(ufile)

        if not attachment_allow:
            get_allow_size = ir_attachment_obj._get_allowed_attachment_size()
            er_msg = 'The file must be less than %s MB' % (get_allow_size)
            args = {'error': _(er_msg)}
            return out % (json.dumps(callback), json.dumps(args))
        get_allow_mimetype = ir_attachment_obj._get_allowed_mimetype_id()
        if ufile.content_type not in get_allow_mimetype:
            er_msg = 'system does not support file format %s' % (
                ufile.content_type)
            args = {'error': _(er_msg)}
            return out % (json.dumps(callback), json.dumps(args))
        res = super(InheritBinary, self).upload_attachment(
            callback, model, id, ufile)
        return res
