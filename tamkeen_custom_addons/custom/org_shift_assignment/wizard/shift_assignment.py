from odoo import models, api, fields, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning


class ShiftAssignment(models.TransientModel):
    _name = 'shift.assignment'
    _description = 'Organization Shift Assignment'

    employee_ids = fields.Many2many('hr.employee',
                                    'employee_shift_assignment_rel',
                                    'shift_assignment_id', 'employee_id',
                                    string='Employee')
    department_ids = fields.Many2many('hr.department',
                                    'department_shift_assignment_rel',
                                    'shift_assignment_id', 'department_id',
                                    string='Department/s')
    cost_center_ids = fields.Many2many('account.analytic.account',
                                      'analytic_account_shift_assignment_rel',
                                      'shift_assignment_id', 'cost_center_id',
                                      string='Cost Center/s')
    category_ids = fields.Many2many('hr.employee.category',
                                       'employee_category_shift_assignment_rel',
                                       'shift_assignment_id', 'category_id',
                                       string='Category/s')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    shift_id = fields.Many2one('resource.calendar', string='Shift ID')
    category = fields.Selection([('by_employee', 'By Employee'),
                                    ('by_department', 'By Department'),
                                    ('by_cost_center', 'By Cost Center'),
                                    ('by_tag', 'By Tag')], string='Category')

    @api.model
    def default_get(self, fields_list):
        res = super(ShiftAssignment, self).default_get(fields_list)
        today = date.today()
        to_date = today + relativedelta(year=9999, day=31, month=12)
        res.update({'date_to': str(to_date), 'date_from': str(today)})
        return res

    def _get_employess(self):
        employee_obj = self.env['hr.employee']
        employee_rec = False
        if self.category == 'by_employee':
            if self.employee_ids:
                employee_rec = self.employee_ids
        elif self.category == 'by_department' and self.department_ids:
            employee_rec = employee_obj.search([('department_id', 'in',
                                  self.department_ids.ids)])
        elif self.category == 'by_cost_center' and self.cost_center_ids:
            employee_rec = employee_obj.search([('job_id.analytic_account_id', 'in',
                                         self.cost_center_ids.ids)])
        elif self.category == 'by_tag' and self.category_ids:
            employee_rec = employee_obj.search([('category_ids', 'in',
                                         self.category_ids.ids)])
        if employee_rec:
            return employee_rec
        else:
            raise Warning(_('No Employee found for %s category. Please '
                             'select another category.')%
                          dict(self._fields['category'].
                               selection).get(self.category))

    @api.multi
    def assign_shift(self):
        obj_shift_timeline = self.env['shift.timeline']
        employee_name = ''
        for rec in self:
            employee_rec = rec._get_employess()
            if employee_rec:
                shift_timeline_rec = obj_shift_timeline.\
                    search([('employee_id', 'in', employee_rec.ids),
                            ('date_from', '<=', rec.date_to),
                            ('date_to', '>=', rec.date_from)])
                if shift_timeline_rec:
                    for timeline in shift_timeline_rec:
                        employee_name += timeline.employee_id.name + ', '
                if employee_name:
                    raise Warning(_('This Employee has timleline with same '
                                    'period. Kindly, Check below employees. '
                                    '\n %s')%employee_name)
                for employee in employee_rec:
                    vals = {
                        'employee_id': employee and employee.id or False,
                        'shift_id': rec.shift_id and rec.shift_id.id or False,
                        'date_from': rec.date_from,
                        'date_to': rec.date_to,
                        'state': 'active'
                    }
                    obj_shift_timeline.create(vals)

