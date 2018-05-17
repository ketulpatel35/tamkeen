from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def button_shift_timeline(self):
        self.ensure_one()
        context = dict(self._context)
        for rec in self:
            context.update({'default_employee_id': rec.id})
            return {
                'name': 'Shift Timeline',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'shift.timeline',
                'target': 'current',
                'context': context,
                'domain': [('employee_id', 'in', self.ids)]
            }


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def button_shift_timeline(self):
        self.ensure_one()
        context = dict(self._context)
        for rec in self:
            context.update({'default_employee_id': rec.employee_id.id})
            return {
                'name': 'Shift Timeline',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'shift.timeline',
                'target': 'current',
                'context': context,
                'domain': [('employee_id', 'in', [self.employee_id.id])]
            }
