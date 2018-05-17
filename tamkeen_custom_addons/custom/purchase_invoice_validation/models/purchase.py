# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    not_allow_more_amount = fields.Boolean('Allow to invoice more than the '
                                           'purchase order amount')
    not_allow_diff_currency = fields.Boolean("Allow related invoice/s "
                                             "to be in same purchase order "
                                             "currency.")


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    not_allow_more_amount = fields.Boolean('Allow to invoice more than '
                                           'the purchase order amount',
                                           default=False)

    not_allow_diff_currency = fields.Boolean("Allow related invoice/s "
                                             "to be in same purchase order "
                                             "currency.",
                                             default=False)
    @api.model
    def default_get(self, fields):
        res = super(PurchaseConfigSettings, self).default_get(fields)
        # set default value for not_allow_more_amount
        query = 'SELECT id FROM purchase_order WHERE not_allow_more_amount = true'
        self.env.cr.execute(query)
        po_rec_not_allow_more_amount = self.env.cr.fetchall()
        if len(po_rec_not_allow_more_amount) > 0:
            res['not_allow_more_amount'] = True
        # set default value for not_allow_diff_currency
        query = 'SELECT id FROM purchase_order WHERE not_allow_diff_currency = true'
        self.env.cr.execute(query)
        po_rec_not_allow_diff_currency = self.env.cr.fetchall()
        if len(po_rec_not_allow_diff_currency) > 0:
            res['not_allow_diff_currency'] = True
        return res

    @api.multi
    def validation_allow_more_amount(self):
        """
        add validation
        - invoice not allow amount more then po
        :return:
        """
        query = 'UPDATE purchase_order SET not_allow_more_amount = false'
        if self.not_allow_more_amount:
            query = 'UPDATE purchase_order SET not_allow_more_amount = true'
        self.env.cr.execute(query)

    @api.multi
    def validation_allow_diff_currency(self):
        """
        Add validation
        - difference currency not allow
        :return:
        """
        query = 'UPDATE purchase_order SET not_allow_diff_currency = false'
        if self.not_allow_diff_currency:
            query = 'UPDATE purchase_order SET not_allow_diff_currency = true'
        self.env.cr.execute(query)