from odoo import models, api, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    responsibility = fields.Html(string='Responsibility')
    deliverable = fields.Html(string='Deliverable')
    is_print_res = fields.Boolean(string='Print Responsibility')
    is_print_delive = fields.Boolean(string='Print Deliverable')
    t_and_c = fields.Html(string='Terms and Conditions')

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder, self).default_get(fields)
        t_and_c = self.env[
            'purchase.config.settings'].get_default_po_values(fields)
        if 't_and_c' in fields:
            res.update({'t_and_c': t_and_c.get('notes')})
        return res


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    notes = fields.Text(string='Notes')

    @api.model
    def get_default_po_values(self, fields):
        conf = self.env['ir.config_parameter']
        return {
            'notes': conf.get_param(
                'purchase_cofig.notes'),
        }

    @api.one
    def set_po_values(self):
        conf = self.env['ir.config_parameter']
        conf.set_param('purchase_cofig.notes', self.notes)
