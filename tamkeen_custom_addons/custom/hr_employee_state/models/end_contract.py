# -*- encoding: utf-8 -*-
from datetime import datetime

from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class employee_set_inactive(models.TransientModel):
    _name = 'hr.contract.end'
    _description = 'Employee De-Activation Wizard'

    @api.model
    def _get_contract(self):

        return self._context.get('active_id')

    # @api.model
    # def _get_employee(self):
    #
    #     contract_id = context.get('end_contract_id', False)
    #     if not contract_id:
    #         return False
    #
    #     data = self.pool.get(
    #         'hr.contract').read(cr, uid, contract_id, ['employee_id'],
    #                             context=context)
    #     return data['employee_id'][0]
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  readonly=True, default=_get_contract)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, readonly=True,
                                  related='contract_id.employee_id')
    date = fields.Date(string='Date', required=True, default=datetime.now().
                       strftime(DEFAULT_SERVER_DATE_FORMAT))
    reason_id = fields.Many2one('hr.employee.termination.reason', 'Reason',
                                required=True)
    notes = fields.Text('Notes')

    @api.multi
    def set_employee_inactive(self):

        # data = self.read(
        #     cr, uid, ids[0], [
        #         'employee_id', 'contract_id', 'date', 'reason_id', 'notes'],
        #     context=context)
        vals = {
            'date': self.date,
            'employee_id': self.employee_id.id,
            'reason_id': self.reason_id.id,
            'notes': self.notes,
        }

        self.contract_id.setup_pending_done(vals)

        return {'type': 'ir.actions.act_window_close'}
