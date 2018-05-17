# -*- coding: utf-8 -*-
import requests
from urlparse import urlparse
from odoo import http
from odoo.http import request
from Crypto.Cipher import XOR
import base64
from odoo.exceptions import UserError
from requests.exceptions import ConnectionError
from odoo import _


class spagobi_app_login(http.Controller):
    @http.route(
        '/bista_spagobi_sso/spagobi_login_url',
        type='json',
        auth='public')
    def spagobi_login_url(self):
        spagobi = request.env['spagobi.config'].search([])
        if spagobi:
            url = spagobi[0].url
        else:
            raise UserError(
                _("Error ! \n SpagoBI configuration setting not done."))
        return {'url': url}

    @http.route('/bista_spagobi_sso/spagobi_login', type='json', auth='public')
    def spagobi_login(self):
        spagobi = request.env['spagobi.config'].search([])
        if spagobi:
            url = spagobi[0].url + 'servlet/AdapterHTTP?PAGE=LoginPage'
            userID = spagobi[0].admin_user
            password = spagobi[0].admin_password
            current_user_id = request.env.uid
            current_user = request.env['res.users'].search(
                [('id', '=', current_user_id)])
            user_id = current_user.id
            user_login = current_user.login
            sso_key = current_user.sso_key

            if user_id == 1:
                if sso_key is False or sso_key == '':

                    try:
                        r = requests.post(url,
                                          data={
                                              'NEW_SESSION': 'True',
                                              'isInternalSecurity': 'true',
                                              'userID': userID,
                                              'password': password})

                    except ConnectionError:  # This is the correct syntax
                        raise UserError("Error ! \n No response")

            else:
                if sso_key is False or sso_key == '':
                    raise UserError("Error ! \n SSO key not generate yet!!!")
                else:
                    encrypted_key = "pbkdf2_sha512"
                    sso_key = self._sso_key_decrypt(encrypted_key, sso_key)

                    try:
                        r = requests.post(
                            url,
                            data={
                                'NEW_SESSION': 'True',
                                'isInternalSecurity': 'true',
                                'userID': user_login,
                                'password': sso_key})

                    except ConnectionError:  # This is the correct syntax
                        raise UserError("Error ! \n No response")

            status = r.status_code
            if status == 200:
                host = urlparse(url)
                subdomain0 = host.hostname.split('.')[1]
                subdomain1 = host.hostname.split('.')[2]
                subdomain = '.' + subdomain0 + '.' + subdomain1
                cookies = requests.utils.dict_from_cookiejar(r.cookies)
                cookies_session = cookies['JSESSIONID']
            else:
                raise UserError(
                    "Error ! \n Please check SpagoBI Web Application "
                    "configuration or contact to you administartor."
                    "\n(Might be configuration is not set.)")

        else:
            raise UserError(
                "Error ! \n Please check SpagoBI Web Application "
                "configuration or contact to you administartor."
                "\n(Might be configuration is not set.)")

        return {'cookies_session': cookies_session, 'subdomain': subdomain}

    def _sso_key_decrypt(self, encrypted_key, sso_key):
        cipher = XOR.new(encrypted_key)
        return cipher.decrypt(base64.b64decode(sso_key))


spagobi_app_login()
