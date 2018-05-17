from odoo import models, api, fields, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning


class ShiftTimeline(models.Model):
    _name = 'shift.timeline'
    _description = 'Shift Timeline'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread']

    def _get_shift(self, employee):
        today_date = date.today()
        shift_timeline_rec = self.search([('date_from', '<=',
                                           str(date.today())),
                                          ('date_to', '>=',
                                           str(today_date)),
                                          ('employee_id', '=', employee.id)],
                                         limit=1)
        shift_rec = False
        if shift_timeline_rec:
            shift_rec = shift_timeline_rec.shift_id
        if not shift_rec:
            if employee and employee.contract_id and \
                    employee.contract_id.working_hours:
                return employee.contract_id.working_hours
        return shift_rec

    def _get_rest_days(self, employee):
        shift_rec = self._get_shift(employee)
        rest_days = []
        if shift_rec:
            rest_days = shift_rec.get_rest_days()
        return rest_days

    @api.model
    def default_get(self, fields_list):
        res = super(ShiftTimeline, self).default_get(fields_list)
        today = date.today()
        to_date = today + relativedelta(year=9999, day=31, month=12)
        res.update({'date_to': str(to_date)})
        return res

    employee_id = fields.Many2one('hr.employee',
                                  string='Employee',
                                  track_visibility='onchange')
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee ID', store=True)
    position_id = fields.Many2one('hr.job',
                                  string='Position',
                                  track_visibility='onchange',
                                  related='employee_id.job_id', store=True)
    organization_unit_id = fields.Many2one('hr.department',
                                        string='Organization Unit',
                                        track_visibility='onchange',
                                        related='employee_id.department_id',
                                        store=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    shift_id = fields.Many2one('resource.calendar', string='Shift ID')
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'),
                              ('closed', 'Closed')],
                             default='draft')

    @api.multi
    def button_active(self):
        for rec in self:
            print rec.employee_id, rec.employee_id.contract_id
            if rec.employee_id and rec.employee_id.contract_id:
                rec.employee_id.contract_id.write({'working_hours':
                                                       rec.shift_id.id})
                rec.write({'state': 'active'})
            else:
                raise Warning(_('Employee should have contract.'))

    @api.multi
    def button_closed(self):
        for rec in self:
            rec.write({'state': 'closed'})