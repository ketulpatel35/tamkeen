from odoo import models, api, fields
from odoo.tools.translate import _
from odoo.exceptions import Warning


class hr_payslip_employees(models.TransientModel):

    _name = 'wage.adjustment.employees'
    _description = 'Generate wage adjustments for selected employees'

    employee_ids = fields.Many2many(
        'hr.employee',
        'hr_employee_wage_group_rel',
        'adjustment_id',
        'employee_id',
        'Employees')

    @api.model
    def _calculate_adjustment(self, initial, adj_type, adj_amount):

        result = 0
        if adj_type == 'fixed':
            result = initial + adj_amount
        elif adj_type == 'percent':
            result = initial + (initial * adj_amount / 100)
        elif adj_type == 'final':
            result = adj_amount
        else:
            # manual
            result = initial

        return result

    @api.multi
    def create_adjustments(self):
        adj_pool = self.env['hr.contract.wage.increment']
        run_pool = self.env['hr.contract.wage.increment.run']

        active_id = self._context.get('active_id', False)
        if not active_id:
            raise Warning(_('Internal Error ! \n Unable to determine wage '
                            'adjustment run ID'))

        for rec in self:
            if not rec.employee_ids:
                raise Warning(_("Warning ! \n You must select at least one "
                                "employee to generate wage adjustments."))
            run_data = run_pool.browse(active_id)
            for emp in rec.employee_ids:
                res = {
                    'effective_date': run_data.effective_date,
                    'contract_id': emp.contract_id.id,
                    'employee_id': emp.id,
                    'wage': self._calculate_adjustment(
                        emp.contract_id.wage,
                        run_data.type,
                        run_data.adjustment_amount),
                    'c_wage': emp.contract_id.wage,
                    'run_id': run_data.id,
                }
                adj_pool.create(res)
        return {'type': 'ir.actions.act_window_close'}
