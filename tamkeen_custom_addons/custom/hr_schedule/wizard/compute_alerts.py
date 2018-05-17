from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, api, fields


class compute_alerts(models.TransientModel):
    _name = 'hr.schedule.alert.compute'
    _description = 'Check Alerts'

    date_start = fields.Date(string='Start')
    date_end = fields.Date(string='End')
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_alert_rel',
                                    'generate_id', 'employee_id',
                                    string='Employees')

    @api.multi
    def generate_alerts(self):

        alert_obj = self.env['hr.schedule.alert']
        dStart = datetime.strptime(self.date_start, '%Y-%m-%d').date()
        dEnd = datetime.strptime(self.date_end, '%Y-%m-%d').date()
        dToday = datetime.strptime(fields.Date.context_today(self),
                                   '%Y-%m-%d').date()
        if dToday < dEnd:
            dEnd = dToday

        dNext = dStart
        for employee_id in self.employee_ids:
            while dNext <= dEnd:
                alert_obj.compute_alerts_by_employee(employee_id,
                                                     dNext.strftime('%Y-%m-%d')
                                                     )
                dNext += relativedelta(days=+1)

            return {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'hr.schedule.alert',
                'domain': [('employee_id', '=', employee_id.id),
                           ('name', '>=', self.date_start + ' 00:00:00'),
                           ('name', '<=', self.date_end + ' 23:59:59')],
                'type': 'ir.actions.act_window',
                'target': 'current',
                'nodestroy': True,
                'context': self._context,
            }
