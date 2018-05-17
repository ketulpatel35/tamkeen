import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo import models, api, fields


class HrAccural(models.Model):
    _name = 'hr.accrual'
    _description = 'Accrual'

    name = fields.Char(string='Name')
    holiday_status_id = fields.Many2one('hr.holidays.status', string='Leave')
    line_ids = fields\
        .One2many('hr.accrual.line',
                  'accrual_id', string='Accrual Lines')

    @api.multi
    def get_balance(self, employee_id, date=None):
        res = 0.0
        self._cr.execute('''SELECT SUM(amount) from hr_accrual_line \
                           WHERE accrual_id in
                            %s AND employee_id=%s
                             AND date <= %s''',
                         (tuple(self._ids),
                          employee_id, date or
                          time.strftime(OE_DATEFORMAT)))
        for row in self._cr.fetchall():
            res = row[0]
        return res


class HrAccrualLine(models.Model):
    _name = 'hr.accrual.line'
    _description = 'Accrual Line'
    _rec_name = 'date'

    date = fields.Date('Date', required=True,
                       default=time.strftime(OE_DATEFORMAT))
    accrual_id = fields.Many2one('hr.accrual', string='Accrual')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    amount = fields.Float(string='Amount')
