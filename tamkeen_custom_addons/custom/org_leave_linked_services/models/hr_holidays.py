from odoo import models, api, fields, _

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    def _count_service_request(self):
        """
        :return:
        """
        for rec in self:
            service_req_count = self.env['service.request'].search_count([
                ('reference_id', '=', str(rec._name) + ',' + str(rec.id))])
            rec.service_request_count = service_req_count

    # additional_service_needed = fields.Boolean(string='Additional Service '
    #                                                   'Needed')
    # additional_services = fields.One2many('service.request', 'leave_id',
    #                                       string='Additional Services')
    service_request_count = fields.Integer('Service Request Count',
                                           compute='_count_service_request')

    @api.multi
    def action_service_management_request(self):
        """
        Open Service Management
        :return:
        """
        res = self.env['ir.actions.act_window'].for_xml_id(
            'service_management', 'act_all_services_with_reference')
        ctx = {'default_reference_id': str(self._name) + ',' + str(self.id),
               'linked_with_leave': True}
        if self.state != 'draft':
            ctx.update({'create': False, 'edit': False, 'delete': False})
        res['context'] = ctx
        return res


class ServiceRequest(models.Model):
    _inherit = 'service.request'


    leave_id = fields.Many2one('hr.holidays', string='Leave')


class ServiceCategory(models.Model):
    _inherit = 'service.category'

    linked_with_leave = fields.Boolean(string='Linked with Leave?')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        args = args or []
        context = dict(self._context)
        if context.get('leave'):
            records = self.search([('linked_with_leave', '=', True)])
            return records.name_get()
        return super(ServiceCategory, self).name_search(name=name, args=args,
                                                        operator=operator,
                                                        limit=limit)

