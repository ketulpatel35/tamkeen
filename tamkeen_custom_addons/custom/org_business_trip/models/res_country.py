from odoo import fields, models, api, _


class ServiceRequest(models.Model):
    _inherit = 'res.country'

    bt_countries_group_id = fields.Many2one('bt.countries.group')

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('want_remaining_country'):
            # bt_c_group_rec = self.env['bt.countries.group'].search([])
            # country_ids = []
            # [country_ids.append(bcg_rec.country_ids.ids) for bcg_rec
            #  in bt_c_group_rec]
            # args.append((('id', 'not in', country_ids)))
            args.append((('bt_countries_group_id', '=', False)))
        return super(ServiceRequest, self).search(
            args, offset=offset, limit=limit, order=order, count=count)