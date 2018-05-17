from odoo import models, api, fields


class department_selection(models.TransientModel):

    _name = 'hr.schedule.validate.departments'
    _description = 'Department Selection for Validation'

    department_ids = fields.Many2many('hr.department',
                                      'hr_department_group_rel',
                                      'employee_id', 'department_id',
                                      string='Departments')

    @api.multi
    def view_schedules(self):
        for data in self:
            for dept in data.department_ids:
                return {
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'hr.schedule',
                    'domain': [('department_id', '=', dept.id),
                               ('state', 'in', ['draft'])],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'nodestroy': True,
                    'context': self._context,
                }

    @api.multi
    def do_validate(self):
        for rec in self:
            for dept in rec.department_ids:
                sched_ids = self.env['hr.schedule'].search([
                    ('department_id', '=', dept.id)])
                for sched_id in sched_ids:
                    sched_id.action_validate()
        return {'type': 'ir.actions.act_window_close'}
