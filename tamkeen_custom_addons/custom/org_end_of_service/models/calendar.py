from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    end_of_service_id = fields.Many2one('org.end.of.service',
                                        string='Org End of Service')