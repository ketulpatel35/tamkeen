# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.translate import _
from odoo.exceptions import Warning, UserError


class hr_transfer(models.Model):
    _name = 'hr.department.transfer'
    _description = 'Departmental Transfer'
    _rec_name = 'date'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('src_id')
    def _get_jobs_src(self):
        for sub_id in self:
            if sub_id.src_id:
                sub_id.src_func = sub_id.src_id.name

    @api.multi
    @api.depends('src_contract_id')
    def _get_contract_src(self):
        for sub_id in self:
            if sub_id.src_contract_id:
                sub_id.src_contract_func = sub_id.src_contract_id.name

    @api.multi
    @api.depends('dst_id')
    def _get_department_dist(self):
        for sub_id in self:
            if sub_id.dst_id.department_id:
                sub_id.dist_department_func = sub_id.dst_id.department_id.name

    @api.multi
    @api.depends('employee_id')
    def _get_department_src(self):
        for sub_id in self:
            if sub_id.state == 'draft':
                if sub_id.employee_id.department_id:
                    sub_id.src_department_func =\
                        sub_id.employee_id.department_id.name
                else:
                    sub_id.src_department_func = None
            else:
                sub_id.src_department_func =\
                    sub_id.employee_id.department_id.name

    employee_id = fields.Many2one('hr.employee', 'Employee')
    src_id = fields.Many2one('hr.job', 'Current Job')
    src_func = fields.Char(compute='_get_jobs_src', string='Current Job')
    dst_id = fields.Many2one('hr.job', 'Destination Job')
    src_department_id = fields.Many2one(related='src_id.department_id',
                                        string='Current Organization Unit',
                                        store=True)
    src_department_func = fields.Char(
        compute='_get_department_src',
        string='Current Department')
    dst_department_id = fields.Many2one(related='dst_id.department_id',
                                        string='Destination Organization Unit',
                                        store=True)
    dist_department_func = fields.Char(
        compute='_get_department_dist',
        string='Destination Department')
    src_contract_id = fields.Many2one('hr.contract', 'Current Contract')
    src_contract_func = fields.Char(
        compute='_get_contract_src',
        string='From Contract')
    dst_contract_id = fields.Many2one('hr.contract', 'New Contract')
    date = fields.Date('Effective Date')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('pending', 'Pending'), ('done', 'Done'),
                              ('cancel', 'Cancelled')], 'State',
                             default='draft')

    @api.multi
    def copy(self, default=None):
        raise UserError(_('You cannot duplicate a Department Transfer.'))

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
        :return:
        """
        self.src_contract_id = False
        self.src_id = False
        if self.employee_id:
            # emp_contract = self._get_employee_contract(self.employee_id)
            emp_contract = self.employee_id.contract_id
            if emp_contract:
                if emp_contract.job_id:
                    self.src_id = emp_contract.job_id.id
                self.src_contract_id = emp_contract.id

    @api.multi
    def _track_subtype(self, init_values):
        #  used to track events
        self.ensure_one()
        if 'state' in init_values and self.state == 'confirm':
            return 'hr_transfer.mt_alert_xfer_confirmed'
        elif 'state' in init_values and self.state == 'pending':
            return 'hr_transfer.mt_alert_xfer_pending'
        elif 'state' in init_values and self.state == 'done':
            return 'hr_transfer.mt_alert_xfer_done'
        return super(hr_transfer, self)._track_subtype(init_values)

    @api.model
    def _needaction_domain_get(self):
        # return domain for hr manager
        domain = []
        users_obj = self.env['res.users']
        if users_obj.has_group('hr.group_hr_manager'):
            domain += [('state', '=', 'confirm')]
            return domain
        return False

    @api.multi
    def unlink(self):
        # will raise the validation error when user tries to deleted record
        # which is not is draft state
        for transfer in self:
            if transfer.state not in ['draft']:
                raise ValidationError(_('Unable to Delete Transfer! Transfer '
                                        'has been initiated. Either cancel '
                                        'the transfer or create another '
                                        'transfer to undo it.'))
        return super(hr_transfer, self).unlink()

    @api.multi
    def signal_confirm(self):
        # call another method from button
        for rec in self:
            self._get_employee_contract(rec.employee_id)
            rec.state_confirm()

    @api.multi
    def effective_date_in_future(self):
        # check the effective date set by user
        today = datetime.now().date()
        for xfer in self:
            effective_date = datetime.strptime(
                xfer.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False
        return True

    @api.model
    def _check_state(self, contract_id, effective_date):
        # check state of contract and also check end date of contract as well
        data = self.env['hr.contract'].browse(contract_id)
        if data and data.state not in ['trial', 'trial_ending', 'open',
                                       'contract_ending']:
            raise ValidationError(_('The current state of the contract '
                                    'does not permit changes.'))
        if data and data.date_end:
            dContractEnd = datetime.strptime(
                data.date_end, DEFAULT_SERVER_DATE_FORMAT).date()
            dEffective = datetime.strptime(
                effective_date, DEFAULT_SERVER_DATE_FORMAT).date()
            if dEffective >= dContractEnd:
                raise ValidationError(_('The contract end date is on or '
                                        'before the effective date of '
                                        'the transfer.'))
        return True

    @api.one
    def transfer_contract(self, contract_id, job_id, effective_date):
        # Copy the contract and adjust start/end dates, job id,
        # etc. accordingly.
        self.ensure_one()
        contract_obj = self.env['hr.contract']
        old_contract_rec = contract_obj.browse(contract_id)
        default = {
            'job_id': job_id,
            'date_start': effective_date,
            'name': old_contract_rec.name,
            'message_ids': False,
            'trial_date_start': False,
            'trial_date_end': False,
            'department_id': self.dst_department_id.id,
        }
        if old_contract_rec:
            data = old_contract_rec.copy_data(default)[0]
            # create new contract
            new_contract_rec = contract_obj.with_context({
                'cr_seq': old_contract_rec.name}).create(data)
            new_contract_rec.write({'wage': old_contract_rec.wage})
            if new_contract_rec:
                # manage new contract history
                new_contract_rec.wage_inc_history_ids = [
                    (4, old_contract_rec.id)]
                vals = {}
                # Set the new contract to the appropriate state
                new_contract_rec.signal_confirm_all()
                if old_contract_rec.state == 'open':
                    new_contract_rec.signal_open()
                # Terminate the current contract (and trigger appropriate state
                # change)
                old_note = old_contract_rec.notes or ''
                notes = old_note + '\nSupercedes (because of Department ' \
                                   'Transfer) previous ' \
                                   'contract: ' + str(old_contract_rec.name)
                vals.update({
                    'is_active': False,
                    'notes': notes,
                    'from_amend': 'Department Transfer',
                })
                vals['date_end'] = datetime.strptime(
                    effective_date, '%Y-%m-%d').date() + relativedelta(days=-1)

                old_contract_rec.write(vals)
                old_contract_rec.state_amendment()
                # Link to the new contract
                self.write({'dst_contract_id': new_contract_rec.id})
        return

    @api.multi
    def state_confirm(self):
        # call check state method to check the state of contract and end
        # date and set transfer to confirm state
        for transfer in self:
            if transfer.src_contract_id:
                transfer._check_state(transfer.src_contract_id.id,
                                      transfer.date)
            transfer.write({'state': 'confirm'})
        return True

    @api.multi
    def signal_pending(self):
        # check the effective date set by user and accoringly it writes state
        for transfer in self:
            if transfer.effective_date_in_future():
                transfer.state_done()
                transfer.write({'state': 'pending'})
            else:
                transfer.state_done()
                transfer.write({'state': 'done'})
        return True

    @api.multi
    def signal_cancel(self):
        # set the state cancel
        for transfer in self:
            transfer.write({'state': 'cancel'})
        return True

    @api.multi
    def state_done(self):
        # write set to done and write updated department id and contract in
        # employee
        today = datetime.now().date()
        for xfer in self:
            if datetime.strptime(xfer.date,
                                 DEFAULT_SERVER_DATE_FORMAT).date() <= today:
                self._check_state(xfer.src_contract_id.id, xfer.date)
                xfer.employee_id.write({
                    'department_id': xfer.dst_id.department_id.id,
                    'parent_id':
                        xfer.dst_id.department_id.manager_id and
                        xfer.dst_id.department_id.manager_id.id or False})
                self.transfer_contract(xfer.src_contract_id.id,
                                       xfer.dst_id.id, xfer.date)
                self.state = 'done'
            else:
                return False
        return True

    @api.model
    def _get_employee_contract(self, employee_rec):
        """
        set proper employee contract
        :return:
        """

        # emp_contract = self.env['hr.contract'].search([
        #     ('employee_id', '=', employee_rec.id), ('is_active', '=', True)])
        if employee_rec:
            emp_contract = employee_rec.contract_id
        if not emp_contract:
            raise Warning(_('contract not found for employee : %s') % (
                employee_rec.name))
        # if len(emp_contract) > 1:
        #     raise Warning(_('multiple contract
        #  not found for this employee : '
        #                     '%s') % (employee_rec.name))
        return emp_contract

    @api.model
    def try_pending_department_transfers(self):
        # Completes pending departmental transfers .Called from the scheduler
        today = datetime.now().date()
        xfer_ids = self.env['hr.department.transfer']. \
            search([('state', '=', 'pending'),
                    ('date', '<=',
                     today.strftime(DEFAULT_SERVER_DATE_FORMAT))])
        for xfer in xfer_ids:
            if not xfer.effective_date_in_future():
                xfer.state_done()
        return True
