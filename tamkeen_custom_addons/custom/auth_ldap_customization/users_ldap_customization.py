# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, models
from odoo import tools
import logging

_logger = logging.getLogger(__name__)


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    @api.model
    def get_or_create_user(self, conf, login, ldap_entry):
        """
        Retrieve an active resource of model res_users with the specified
        login. Create the user if it is not initially found.

        :param dict conf: LDAP configuration
        :param login: the user's login
        :param tuple ldap_entry: single LDAP result (dn, attrs)
        :return: res_users id
        :rtype: int
        """

        user_id = False
        login = tools.ustr(login.lower())
        self.env.cr.execute("SELECT id,"
                            " active FROM res_users WHERE"
                            " lower(login)=%s", (login,))
        res = self.env.cr.fetchone()
        if res:
            if res[1]:
                user_id = res[0]
        elif conf['create_user']:
            _logger.debug("Creating new Odoo user \"%s\" from LDAP" % login)
            values = self.map_ldap_attributes(conf, login, ldap_entry)
            SudoUser = self.env['res.users'].sudo()
            if conf['user']:
                values['active'] = True
                values['email'] = ldap_entry[1]['mail'][0].lower()
                user_id = SudoUser. \
                    browse(conf['user'][0]).copy(default=values).id
                '''NOTE --> Check if the employee
                 exists by searching him using
                  his email got from LDAP information
                , If employee exists...Create him a User
                 and link this user by updating the employee
                  record with the new created user_id and
                   the work phone (extension)
                , If not...He can't log in and a message
                 will appear to the user
                  (Invalid user or password) '''
            employee_rec = self.env['hr.employee'].search([
                ('work_email', '=ilike', ldap_entry[1]['mail'][0].lower())])
            if employee_rec:
                values['email'] = ldap_entry[1]['mail'][0].lower()
                if not user_id:
                    user_id = SudoUser.create(values).id
                employee_rec. \
                    write({'user_id': user_id,
                           'work_phone': ldap_entry[1]['telephoneNumber']
                           [0] if ldap_entry[1].get('telephoneNumber')
                           else False})
        return user_id