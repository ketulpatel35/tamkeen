from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api


class hr_schedule_generate(models.TransientModel):

    _name = 'hr.schedule.generate'
    _description = 'Generate Schedules'

    date_start = fields.Date(string='Start')
    no_weeks = fields.Integer(string='Number of weeks', default='2')
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_schedule_rel',
                                    'generate_id', 'employee_id',
                                    string='Employees')

    @api.onchange('date_start')
    def onchange_start_date(self):
        if self.date_start:
            dStart = datetime.strptime(self.date_start, '%Y-%m-%d').date()
            # The schedule must start on a Monday
            if dStart.weekday() == 0:
                self.date_start = dStart.strftime('%Y-%m-%d')

    @api.multi
    def generate_schedules(self):
        sched_obj = self.env['hr.schedule']
        dStart = datetime.strptime(self.date_start, '%Y-%m-%d').date()
        dEnd = dStart + relativedelta(weeks=+self.no_weeks, days=-1)

        sched_ids = []
        for ee in self.employee_ids:
            if not ee.contract_id or not ee.contract_id.working_hours:
                continue
            sched = {
                'name': ee.name + ': ' + self.date_start + ' Wk ' +
                str(dStart.isocalendar()[1]),
                'employee_id': ee.id,
                'template_id': ee.contract_id.working_hours.id,
                'date_start': dStart.strftime('%Y-%m-%d'),
                'date_end': dEnd.strftime('%Y-%m-%d'),
            }
            sch = sched_obj.create(sched)
            sched_ids.append(
                sch.id)
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.schedule',
            'domain': [('id', 'in', sched_ids)],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'nodestroy': True,
            'context': self._context,
        }
