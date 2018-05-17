# -*- encoding: utf-8 -*-
import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import fields, models, api
import logging

_l = logging.getLogger(__name__)


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = ['hr.contract', 'mail.thread', 'ir.needaction_mixin']

    # @api.multi
    # def _get_ids_from_employee(self):
    #
    #     # res = []
    #     # for ee in self.pool.get('hr.employee').browse(cr, uid, ids,
    # context=context):
    #     #     for contract in ee.contract_ids:
    #     #         if contract.state not in ['pending_done', 'done']:
    #     #             res.append(contract.id)
    #     # return res
    #
    #     res = []
    #     for ee in self.env['hr.employee']:
    #         print"dsdsddsdds__________________",ee
    #         #for contract in ee.contract_ids:
    #             #if contract.state not in ['pending_done', 'done']:
    #                 #res.append(contract.id)
    #     return res

    # @api.multi
    # def _get_department(self,field_name, arg):
    #
    #     res = dict.fromkeys(self._ids, False)
    #     # for contract in self.browse(cr, uid, ids, context=context):
    #     #     if contract.department_id and contract.state in [
    # 'pending_done', 'done']:
    #     #         res[contract.id] = contract.department_id.id
    #     #     elif contract.employee_id.department_id:
    #     #         res[contract.id] = contract.employee_id.department_id.id
    #     # return res
    #
    #     for contract in self:
    #         if contract.department_id and contract.state in ['pending_done',
    #  'done']:
    #             res[contract.id] = contract.department_id.id
    #         elif contract.employee_id.department_id:
    #             res[contract.id] = contract.employee_id.department_id.id
    #     return res
    #
    state = fields.Selection([('draft', 'Draft'),
                              ('trial', 'Trial'),
                              ('trial_ending', 'Trial Period Ending'),
                              ('open', 'Open'),
                              ('contract_ending', 'Ending'),
                              ('renew', 'Renew'),
                              ('pending_done', 'Pending Termination'),
                              ('amendment', 'Amendment'),
                              ('close', 'Completed')],
                             strinig='State',
                             defaults='draft')

    # store this field in the database and trigger a change only if the
    # contract is
    # in the right state: we don't want future changes to an employee's
    # department to
    # impact past contracts that have now ended. Increased priority to
    # override hr_simplify.
    # version 10 have already department_id and remaning to migrated
    # department_id = fields.Many2one(compute=_get_department, method=True,
    # obj='hr.department', string="Department",
    # store={
    #  'hr.employee': (_get_ids_from_employee,
    #  ['department_id'], 10)})

    # At contract end this field will hold the job_id, and the
    # job_id field will be set to null so that modules that
    # reference job_id don't include deactivated employees.
    end_job_id = fields.Many2one('hr.job', string='Job Title')

    # The following are redefined again to make them editable only in
    # certain states
    # employee_id = fields.Many2one('hr.employee', string="Employee",
    #                               states={
    #                                   'draft': [('readonly', False)]})
    # type_id = fields.Many2one('hr.contract.type', string="Contract Type",
    #                           required=True, readonly=True,
    #                           states={'draft': [('readonly', False)]})
    # date_start = fields.Date(string='Start Date')
    # wage = fields.Float(string='Wage', digits=(16, 2), required=True,
    #                     readonly=True,
    #                     states={'draft': [('readonly', False)]},
    #                     help="Basic Salary of the employee")

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'trial_ending':
            return 'hr_contract_state.mt_alert_trial_ending'
        elif 'state' in init_values and self.state == 'open':
            return 'hr_contract_state.mt_alert_open'
        elif 'state' in init_values and self.state == 'contract_ending':
            return 'hr_contract_state.mt_alert_contract_ending'
        return super(hr_contract, self)._track_subtype(init_values)

    # @api.onchange('job_id')
    # def onchange_job(self):
    #     # import logging
    #     # _l = logging.getLogger(__name__)
    #     # _l.warning('hr_contract_state: onchange_job()')
    #     # res = False
    #     for contract_rec in self:
    #         if contract_rec.state == 'draft':
    #             return super(hr_contract, self).onchange_job()

    @api.multi
    def condition_trial_period(self):
        today = datetime.today()
        for contract in self:
            if not contract.trial_date_start or datetime.strptime(
                    contract.trial_date_end, OE_DFORMAT) < today:
                return False
        return True

    @api.model
    def try_signal_ending_contract(self):

        d = datetime.now().date() + relativedelta(days=+30)
        ids = self.search([
            ('state', '=', 'open'),
            ('date_end', '<=', d.strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ])
        if len(ids) == 0:
            return

        for contract in ids:
            contract.state = 'contract_ending'

        return

    @api.model
    def try_signal_contract_completed(self):
        d = datetime.now().date()
        ids = self.search([
            ('state', '=', 'open'),
            ('date_end', '<', d.strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ])
        if len(ids) == 0:
            return

        for contract in ids:
            contract.state_pending_done()
        return

    @api.model
    def try_signal_ending_trial(self):
        d = datetime.now().date() + relativedelta(days=+10)
        ids = self.search([
            ('state', '=', 'trial'),
            ('trial_date_end', '<=', d.strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ])
        if len(ids) == 0:
            return
        for contract in ids:
            contract.state = 'trial_ending'
        return

    @api.model
    def try_signal_open(self):

        d = datetime.now().date() + relativedelta(days=-5)
        ids = self.search([
            ('state', '=', 'trial_ending'),
            ('trial_date_end', '<=', d.strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ])
        if len(ids) == 0:
            return

        for contract in ids:
            contract.signal_open()
        return

    @api.onchange('date_start')
    def onchange_start(self):
        for rec in self:
            rec.trial_date_start = rec.date_start

    @api.multi
    def state_trial(self):
        for rec in self:
            rec.write({'state': 'trial'})
        return True

    @api.multi
    def signal_confirm(self):
        for contract in self:
            if contract.condition_trial_period():
                contract.state_trial()
            else:
                contract.signal_open()

    @api.multi
    def signal_open(self):
        for contract in self:
            contract.state = 'open'

    @api.multi
    def state_pending_done(self):
        for rec in self:
            rec.state = 'pending_done'
        return True

    @api.multi
    def signal_confirm_all(self):
        # this Temp Function just to help Hr Emp. to confirm all contract
        job_ids = self.search([('state', '=', 'draft')])
        for contract in job_ids:
            if contract.condition_trial_period:
                contract.state_trial()

        return True

    @api.multi
    def state_amendment(self):
        for rec in self:
            rec.state = 'amendment'

    @api.multi
    def state_close(self):
        """
        :return:
        """
        context = dict(self._context)
        for rec in self:
            vals = {'state': 'close',
                    'date_end': False,
                    # 'job_id': False,
                    'end_job_id': rec.job_id.id}
            if context.get('termination') and context.get('term_date'):
                vals['date_end'] = context.get('term_date')
            elif rec.date_end:
                vals['date_end'] = rec.date_end
            else:
                vals['date_end'] = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
            rec.write(vals)
        return True

    @api.multi
    def state_renew(self):
        for rec in self:
            if rec.state == 'contract_ending':
                rec.write({'state': 'renew'})
                contract_rec = rec.copy()
                contract_rec.date_end = False
        return rec
