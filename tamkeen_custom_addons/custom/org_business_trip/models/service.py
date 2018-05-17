from odoo import fields, models, api, _


class ServiceRequest(models.Model):
    _inherit = 'service.request'

    @api.onchange('service_category_id', 'employee_id')
    def onchange_service_category_id(self):
        """
        :return:
        """
        res = super(ServiceRequest, self).onchange_service_category_id()
        if self._context and self._context.get('linked_with_business_trip'):
            if not res or not res.get('domain', False) or not \
                    res['domain'].get('service_category_id', False):
                res = {'domain': {'service_category_id': []}}
            current_domain = res['domain']['service_category_id']
            new_domain = \
                current_domain + [('linked_with_business_trip', '=', True)]
            res['domain']['service_category_id'] = new_domain
            if self.service_category_id:
                res['domain']['service_type_id'] = [
                    ('service_category_id', '=', self.service_category_id.id)]

        return res


class ServiceCategory(models.Model):
    _inherit = 'service.category'

    linked_with_business_trip = fields.Boolean(
        string='Linked with Business Trip?')
