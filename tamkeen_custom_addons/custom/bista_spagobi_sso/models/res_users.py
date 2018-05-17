# -*- coding: utf-8 -*-

import logging
from passlib.context import CryptContext
import odoo
from odoo import api, fields, models, _
from odoo.addons.base.res import res_users
from Crypto.Cipher import XOR
import base64
import psycopg2
from odoo.exceptions import UserError
from odoo.http import request
import datetime

res_users.USER_PRIVATE_FIELDS.append('password_crypt')

_logger = logging.getLogger(__name__)

default_crypt_context = CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'md5_crypt'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
    deprecated=['md5_crypt'],
)


class ResUsers(models.Model):
    _inherit = "res.users"
    sso_key = fields.Char(string='SSO Encrypted Password')
    spagobi_active = fields.Boolean(
        string='SpagoBI Active',
        default=False,
        help="Check this box if you want to active SpagoBI for current user.")
    spagobi_role = fields.Many2one(
        'spagobi.role',
        string='SpagoBI User Role',
        help="SpagoBI Role will be assign on SpagoBI")

    @api.onchange('active')
    def check_change(self):
        """#SpagoBI user active and deactive from res user form."""
        auto_active = None
        if not self.active:
            spagobi = request.env['spagobi.config'].search([])
            if (spagobi and self.spagobi_active):
                self.spagobi_active = False
                spagobi_status = False
                spagobi_role = self.spagobi_role
                self.spagobi_connection(
                    spagobi_status, spagobi_role, auto_active)
                self.spagobi_role = ""

    @api.model
    def create(self, vals):
        result = None
        spagobi = request.env['spagobi.config'].search([])
        spagobi_status = spagobi.auto_spagobi_active
        default_password = spagobi.default_password
        spagobi_role = spagobi.default_role

        """#If auto active on than spagobi defualt password and role will be
        add on SpagoBI Server.
        #If auto not active than we can active user from Res_user form."""

        if spagobi_status:
            vals["spagobi_active"] = spagobi_status
            vals["spagobi_role"] = spagobi_role.ext_role_id
            encrypted_key = "pbkdf2_sha512"
            sso_key = self._sso_key(encrypted_key, default_password)
            vals["sso_key"] = sso_key
            result = super(ResUsers, self).create(vals)
            auto_active = (vals["login"], sso_key)
            self.spagobi_connection(spagobi_status, spagobi_role, auto_active)

        else:
            if vals["spagobi_active"]:
                raise UserError(
                    _("Error ! \n Uncheck SpagoBI Active."
                      "First generate password than checked this fields."))
            elif vals["spagobi_role"]:
                raise UserError(
                    _("Error ! \n First generate password than select"
                      "this fields role."))
            result = super(ResUsers, self).create(vals)

        return result

    @api.multi
    def write(self, vals):
        result = super(ResUsers, self).write(vals)
        auto_active = None
        if (self.spagobi_active and self.active):
            if not self.sso_key:
                raise UserError(
                    _("Error ! \n Please generate your password by using"
                      "change password."))
            else:
                if self.id != 1:
                    spagobi_status = self.spagobi_active
                    self.spagobi_connection(
                        spagobi_status, self.spagobi_role, auto_active)
        else:
            spagobi = request.env['spagobi.config'].search([])
            if (spagobi and self.spagobi_active is False):
                spagobi_status = self.spagobi_active
                self.spagobi_connection(
                    spagobi_status, self.spagobi_role, auto_active)

            else:
                self.spagobi_active = False
                self.spagobi_role = ''

        return result

    @api.model
    def spagobi_connection(self, spagobi_status, spagobi_role, auto_active):
        """connect spagobi postgres database
        #Create, Update, delete spagobi user
        # 1) Table name :- sbi_user
        # user_id , password, full_name(optional), id, is_superadmin,
        user_in, time_in, sbi_version_in, organization
        # Explaination:-
        # username, password, full name(optional), autoincrement,
        true/false, who crearted, time, verion(4.0), SPAGOBI

        # 2) Table name :- sbi_ext_user_roles
        # id, ext_role_id, user_in, time_in, sbi_version_in, organization
        # Explaination:-
        # autoincrement, role id, who crearted, time, verion(4.0), SPAGOBI"""
        user_in = None

        try:
            spagobi = request.env['spagobi.config'].search([])
            dbname = spagobi.dbname
            host = spagobi.host
            user = spagobi.user
            port = spagobi.port
            password = spagobi.password
            user_in = spagobi.admin_user
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                port=port,
                host=host,
                password=password)

        except:
            if spagobi:
                raise UserError(
                    _("Error ! \n I am unable to connect to the database"))
            else:
                raise UserError(
                    _("Error ! \n SpagoBI configuration setting not done."))

        cur = conn.cursor()
        self.query_execution(
            conn,
            cur,
            spagobi_role,
            spagobi_status,
            user_in,
            auto_active)

        return

    def query_execution(
            self,
            conn,
            cur,
            spagobi_role,
            spagobi_status,
            user_in,
            auto_active):
        """# If we connect on spagobi postgres server we can create,
        update and delete user by this query_execution"""

        sso_user_id = None
        default_role_id = 4
        user_login = self.login
        try:

            if self.login:
                cur.execute(
                    "SELECT id from sbi_user where user_id=%(user_id)s",
                    ({"user_id": self.login}))
                sso_user_id = cur.fetchall()

        except:
            print "I can't SELECT from user"

        ext_role_id = spagobi_role.ext_role_id
        time_in = datetime.datetime.now()

        if spagobi_status:
            encrypted_key = "pbkdf2_sha512"
            spagobi_sso_key = self.sso_key

            if not spagobi_sso_key:
                spagobi_sso_key = auto_active[1]
            if not user_login:
                user_login = auto_active[0]

            spagobi_password = self._sso_pass(encrypted_key, spagobi_sso_key)

            if sso_user_id:
                cur.execute("UPDATE sbi_user SET user_id=%(user_id)s,"
                            "password=%(password)s WHERE id=%(sso_user_id)s",
                            ({"user_id": user_login,
                              "password": spagobi_password,
                              "sso_user_id": sso_user_id[0][0]}))
                cur.execute("DELETE FROM sbi_ext_user_roles WHERE id = %("
                            "id)s", ({"id": sso_user_id[0][0]}))
                cur.execute("INSERT INTO sbi_ext_user_roles (id, "
                            "ext_role_id,user_in, time_in, sbi_version_in, "
                            "organization) values(%(id)s,%(ext_role_id)s,"
                            "%(user_in)s,%(time_in)s,'4.0','SPAGOBI')",
                            ({
                                "id": sso_user_id[0][0],
                                "ext_role_id": ext_role_id,
                                "user_in": user_in,
                                "time_in": time_in
                            }))
                cur.execute("INSERT INTO sbi_ext_user_roles (id, "
                            "ext_role_id,user_in, time_in, sbi_version_in, "
                            "organization) values(%(id)s,%(ext_role_id)s,"
                            "%(user_in)s,%(time_in)s,'4.0','SPAGOBI')",
                            ({
                                "id": sso_user_id[0][0],
                                "ext_role_id": default_role_id,
                                "user_in": user_in,
                                "time_in": time_in
                            }))
                conn.commit()
                conn.close()

            else:
                cur.execute("SELECT max(id)+1 FROM sbi_user")
                new_id = cur.fetchall()
                cur.execute("INSERT INTO sbi_user (user_id, password,"
                            "full_name, id, is_superadmin, user_in, time_in,"
                            "sbi_version_in, organization) values(%("
                            "user_id)s,%(password)s,%(user_id)s,%(id)s,"
                            "False,%(user_in)s,%(time_in)s,'4.0',"
                            "'SPAGOBI')", ({"id": new_id[0][0],
                                            "user_id": user_login,
                                            "password": spagobi_password,
                                            "user_in": user_in,
                                            "time_in": time_in}))
                cur.execute("INSERT INTO sbi_ext_user_roles (id, "
                            "ext_role_id,user_in, time_in, sbi_version_in, "
                            "organization) values(%(id)s,%(ext_role_id)s,"
                            "%(user_in)s,%(time_in)s,'4.0','SPAGOBI')",
                            ({
                                "id": new_id[0][0],
                                "ext_role_id": ext_role_id,
                                "user_in": user_in,
                                "time_in": time_in
                            }))
                cur.execute("INSERT INTO sbi_ext_user_roles (id, "
                            "ext_role_id,user_in, time_in, sbi_version_in, "
                            "organization) values(%(id)s,%(ext_role_id)s,"
                            "%(user_in)s,%(time_in)s,'4.0','SPAGOBI')",
                            ({
                                "id": new_id[0][0],
                                "ext_role_id": default_role_id,
                                "user_in": user_in,
                                "time_in": time_in
                            }))
                conn.commit()
                conn.close()

        else:

            if sso_user_id:
                cur.execute(
                    "DELETE FROM sbi_user WHERE id = %(id)s", ({
                        "id": sso_user_id[0][0]}))
                cur.execute("DELETE FROM sbi_ext_user_roles WHERE id = %("
                            "id)s", ({"id": sso_user_id[0][0]}))
                conn.commit()
                conn.close()

        return

    @api.model
    def check_credentials(self, password):
        # convert to base_crypt if needed
        """# SpagoBI SSO module active than on change password we set sso
        key changs done on this function."""
        self.env.cr.execute('SELECT password, password_crypt FROM res_users '
                            'WHERE id=%s AND active',
                            (self.env.uid,
                             ))
        encrypted = None
        user = self.env.user
        if self.env.cr.rowcount:
            stored, encrypted = self.env.cr.fetchone()
            if stored and not encrypted:
                user._set_password(stored)
                self.invalidate_cache()
        try:
            return super(ResUsers, self).check_credentials(password)
        except odoo.exceptions.AccessDenied:
            if encrypted:
                valid_pass, replacement \
                    = user._crypt_context().verify_and_update(password,
                                                              encrypted)
                if replacement is not None:
                    user._set_encrypted_password(replacement, password)
                if valid_pass:
                    return
            raise

    def _set_password(self, password):
        """# SpagoBI sso module active we set sso key on res user."""
        self.ensure_one()
        """ Encrypts then stores the provided plaintext password for the user
        ``self``
        """
        encrypted = self._crypt_context().encrypt(password)
        self._set_encrypted_password(encrypted, password)

    def _set_encrypted_password(self, encrypted, password):
        """ Store the provided encrypted password to the database, and clears
        any plaintext password
        """
        """#SpagoBI sso module encryt defualt password and set on sso key
        field."""
        encrypted_key = "pbkdf2_sha512"

        sso_key = self._sso_key(encrypted_key, password)

        if self.id == 1:

            self.env.cr.execute(
                "UPDATE res_users SET password='', sso_key='', "
                "password_crypt=%s WHERE id=%s",
                (encrypted, self.id))
        else:

            self.env.cr.execute(
                "UPDATE res_users SET password='', sso_key=%s, "
                "password_crypt=%s WHERE id=%s",
                (sso_key, encrypted, self.id))

    def _crypt_context(self):
        """ Passlib CryptContext instance used to encrypt and verify
        passwords. Can be overridden if technical, legal or political matters
        require different kdfs than the provided default.

        Requires a CryptContext as deprecation and upgrade notices are used
        internally
        """
        return default_crypt_context

    def _sso_key(self, encrypted_key, password):
        """#spagobi sso module sso key encode"""
        cipher = XOR.new(encrypted_key)
        return base64.b64encode(cipher.encrypt(password))

    def _sso_pass(self, encrypted_key, spagobi_sso_key):
        """#spagobi sso module sso key decrypt """
        cipher = XOR.new(encrypted_key)
        return cipher.decrypt(base64.b64decode(spagobi_sso_key))

    @api.onchange('spagobi_active')
    def onchange_spagobi_active(self):
        if not self.spagobi_active:
            self.spagobi_role = ''

    @api.multi
    def unlink(self):
        spagobi = request.env['spagobi.config'].search([])
        if (spagobi and self.spagobi_active):
            auto_active = None
            spagobi_status = False
            spagobi_role = self.spagobi_role
            self.spagobi_connection(spagobi_status, spagobi_role, auto_active)

        result = super(ResUsers, self).unlink()

        return result
