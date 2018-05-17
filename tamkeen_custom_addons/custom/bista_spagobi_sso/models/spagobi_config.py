# -*- encoding: utf-8 -*-

from odoo.http import request
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from urlparse import urlparse
from lxml import etree
import psycopg2


class spagobi_config(models.Model):
    """#SpagoBI SSO module dashborad fields"""
    _name = "spagobi.config"
    _description = "SpagoBI Web Application Configuration"
    _rec_name = 'url'

    url = fields.Char(
        string='URL',
        required=True,
        help="Enter SpagoBI Web Application url here")
    dbname = fields.Char(
        string='DB Name',
        required=True,
        help="Enter SpagoBI Web Application postgresql DB name here")
    host = fields.Char(
        string='DB Host',
        required=True,
        help="Enter SpagoBI Web Application postgresql host name here")
    port = fields.Char(
        string='DB Port',
        required=True,
        help="Enter SpagoBI Web Application postgresql port name here")
    user = fields.Char(
        string='DB User',
        required=True,
        help="Enter SpagoBI Web Application postgresql user id here")
    password = fields.Char(
        string='DB Password',
        required=True,
        help="Enter SpagoBI Web Application postgresql password here")
    admin_user = fields.Char(
        string='Admin User',
        required=True,
        help="Enter SpagoBI Web Application Admin user id here")
    admin_password = fields.Char(
        string='Admin Password',
        required=True,
        help="Enter SpagoBI Web Application Admin password here")
    auto_spagobi_active = fields.Boolean(
        string='Auto SpagoBI Active',
        default=False,
        help="Check this box if you want to active SpagoBI for current user.")
    default_password = fields.Char(
        string='Default Password',
        help="Enter SpagoBI default user password here")
    default_role = fields.Many2one(
        'spagobi.role',
        string='Enter default SpagoBI User Role',
        help="SpagoBI default role will be assign on SpagoBI")

    @api.model
    def create(self, vals):
        """#SpagoBI SSO configuration validation on url"""
        url = vals["url"]
        parse_url = urlparse(url)

        if (parse_url.scheme == "http" or parse_url.scheme == "https"):
            spagobi = request.env['spagobi.config'].search_count([])
            """#spagobi creating only on record in dashboard"""
            if spagobi == 1:
                raise UserError(
                    _("Error ! \n URL ID at backend is must be 1 always"))
            res = super(spagobi_config, self).create(vals)
        else:
            raise UserError(_("Error ! \n URL invalid scheme."))

        return res

    @api.multi
    def write(self, vals):
        res = super(spagobi_config, self).write(vals)
        url = self.url
        parse_url = urlparse(url)
        if parse_url.scheme not in ['http', 'https']:
            raise UserError(_("Error ! \n URL invalid scheme."))

        return res

    @api.model
    def fields_view_get(
            self,
            view_id=None,
            view_type='form',
            toolbar=False,
            submenu=False):
        res = super(
            spagobi_config,
            self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        sql_query = """select * from spagobi_config"""
        self.env.cr.execute(sql_query)
        show_create_edit = self.env.cr.fetchone()

        if show_create_edit > 1:
            doc = etree.XML(res['arch'])
            for t in doc.xpath("//" + view_type):
                t.attrib['create'] = 'false'
            res['arch'] = etree.tostring(doc)

        return res

    @api.onchange('auto_spagobi_active')
    def onchange_auto_spagobi_active(self):
        if not self.auto_spagobi_active:
            self.default_password = ''
            self.default_role = ''

    @api.multi
    def action_role_syncup(self):
        try:
            spagobi = request.env['spagobi.config'].search([])
            dbname = spagobi.dbname
            host = spagobi.host
            user = spagobi.user
            password = spagobi.password
            port = spagobi.port

            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                port=port,
                host=host,
                password=password)
        except:
            raise UserError(
                _("Error ! \n I am unable to connect to the database"))

        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT ext_role_id, name, role_type_cd from sbi_ext_roles")
        except:
            print "I can't SELECT from user"

        sso_roles = cur.fetchall()
        sql_query = """select ext_role_id, name, role_type_cd from
        spagobi_role"""
        self.env.cr.execute(sql_query)
        spagobi_roles = self.env.cr.fetchall()

        list1 = []

        for spagobi_role in spagobi_roles:
            list1.append((spagobi_role[0], spagobi_role[1], spagobi_role[2]))

        list2 = []

        for role in sso_roles:
            list2.append((role[0], role[1], role[2]))

        update_roles = set(list2) & set(list1)
        if update_roles:
            for update_role in update_roles:
                sql_query = """UPDATE spagobi_role SET
                ext_role_id=%(ext_role_id)s, name=%(name)s,
                role_type_cd=%(role_type_cd)s WHERE
                ext_role_id=%(ext_role_id)s"""
                self.env.cr.execute(sql_query, ({'ext_role_id': update_role[0],
                                                 'name': update_role[1],
                                                 'role_type_cd': update_role[
                                                     2]}))

        insert_roles = set(list2) - set(list1)
        if insert_roles:
            for insert_role in insert_roles:
                sql_query = """INSERT INTO spagobi_role (ext_role_id, name,
                role_type_cd) VALUES (%(ext_role_id)s,%(name)s,
                %(role_type_cd)s)"""
                self.env.cr.execute(sql_query, ({'ext_role_id': insert_role[0],
                                                 'name': insert_role[1],
                                                 'role_type_cd': insert_role[
                                                     2]}))


spagobi_config()


class spagobi_role(models.Model):
    _name = "spagobi.role"
    _description = "SpagoBI Role syncup"

    ext_role_id = fields.Integer(
        string='EXT Role ID',
        required=True,
        help="Enter Third Party Web Application EXT Role ID here")
    name = fields.Char(
        string='Name',
        required=True,
        help="Enter Third Party Web Application role name here")
    role_type_cd = fields.Char(
        string='Role Type CD',
        required=True,
        help="Enter Third Party Web Application Role Type CD here")


spagobi_role()
