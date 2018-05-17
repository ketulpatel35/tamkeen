from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def button_dependent(self):
        self.ensure_one()
        context = dict(self._context)
        for rec in self:
            context.update({'default_employee_id': rec.id})
            return {
                'name': 'Dependants',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'employee.family.info',
                'target': 'current',
                'context': context,
                'domain': [('employee_id', 'in', self.ids)]
            }
