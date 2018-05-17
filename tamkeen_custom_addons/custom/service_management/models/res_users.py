# -*- coding: utf-8 -*-
#############################################################################

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def default_get(self, fields):
        """
        :param fields:
        :return:
        """
        result = super(ResUsers, self).default_get(fields=fields)
        # dataobj = self.env['ir.model.data']
        try:
            # dummy, group_id = dataobj.get_object_reference(
            #     'service_management', 'group_service_user')
            # group_rec = self.env['res.groups'].browse(group_id)
            res = {}
            res.update({'tz': result.get('tz')})
            res.update({'company_id': result.get('company_id')})
            res.update({'company_ids': result.get('company_ids')})
            res.update({'notify_email': result.get('notify_email')})
            res.update({'active': result.get('active')})
            res.update({'companies_count': result.get('companies_count')})
            res.update({'lang': result.get('lang')})
            res.update({'share': False})
            return res

        except ValueError:
            pass
        return result
