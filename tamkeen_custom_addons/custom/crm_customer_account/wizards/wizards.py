# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Lead2opportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.model
    def default_get(self, fields_list):
        res = super(Lead2opportunityPartner, self).default_get(fields_list)
        if self._context:
            if self._context.get('default_client_type'):
                if self._context.get('default_client_type') == 'existing':
                    res.update({'action': 'exist'})
                elif self._context.get('default_client_type') == 'prospect':
                    res.update({'action': 'create'})
                else:
                    res.update({'action': 'nothing'})
        return res
