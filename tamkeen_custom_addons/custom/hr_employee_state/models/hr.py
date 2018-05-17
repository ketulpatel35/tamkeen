# -*- encoding: utf-8 -*-
from datetime import datetime
import time
from odoo.exceptions import Warning as UserError
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.translate import _


class hr_employee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    # 'state' is already being used by hr_attendance
    status = fields.Selection([
        ('new', 'New-Hire'),
        ('onboarding', 'On-Boarding'),
        ('active', 'Active'),
        ('pending_inactive', 'Pending Deactivation'),
        ('inactive', 'Inactive'),
        ('reactivated', 'Re-Activated'),
    ], string='Status', default='new')
    inactive_ids = fields.One2many('hr.employee.termination',
                                   'employee_id',
                                   string='Deactivation Records')
    saved_department_id = fields.Many2one('hr.department',
                                          string='Saved Organization Unit')

    @api.multi
    def signal_reactivate(self):
        for rec in self:
            rec.write({'active': True, 'status': 'onboarding'})

    @api.multi
    def action_set_inactive(self):
        for rec in self:
            vals = {
                'active': False,
                'status': 'inactive',
                # 'job_id': False,
            }
            if rec.status == 'pending_inactive':
                vals.update(
                    {'saved_department_id': rec.department_id.id})
            rec.write(vals)
            # rec.department_id = False

    @api.multi
    def signal_confirm(self):
        hr_contract_obj = self.env['hr.contract']
        for rec in self:
            releted_contract = hr_contract_obj.search([
                ('employee_id', '=', rec.id)])
            if not releted_contract:
                raise UserError(('you can not confirm employee without a '
                                 'contract!'))
            rec.write({'status': 'onboarding'})

    @api.multi
    def signal_active(self):
        for rec in self:
            if rec.status == 'pending_inactive':
                rec.write({
                    'status': 'active',
                    'department_id': self.saved_department_id.id
                })
                # rec.saved_department_id = False
            else:
                rec.write({'status': 'active'})

    @api.multi
    def act_pending_inactive(self):
        for rec in self:
            rec.write({'status': 'active'})

    @api.multi
    def state_pending_inactive(self):

        # data = self.read(cr, uid, ids, ['department_id'], context=context)
        for rec in self:
            rec.status = 'pending_inactive'
            rec.saved_department_id = \
                rec.department_id and self.department_id.id or False
            # rec.department_id = False
        return True


class hr_employee_termination_reason(models.Model):
    _name = 'hr.employee.termination.reason'
    _description = 'Reason for Employment Termination'

    name = fields.Char(string='Name')


class hr_employee_termination(models.Model):
    _name = 'hr.employee.termination'
    _description = 'Data Related to Deactivation of Employee'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'employee_id'

    ref = fields.Char('Reference')
    date = fields.Date(string='Effective Date')
    reason_id = fields.Many2one('hr.employee.termination.reason',
                                string='Reason')
    notes = fields.Text(string='Notes')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    emp_company_id = fields.Char('Employee Company Id',
                                 related='employee_id.f_employee_no')
    saved_department_id = fields.Many2one('hr.department', string="Department")
    # request_date = fields.Date(string='Request Date')
    notice_period = fields.Integer(string='Notice Period')
    ffs = fields.Boolean(string='FFS')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('deactive_user', 'User Deactivated'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),
    ], string='State', default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        ref = self.env['ir.sequence'].next_by_code('seq.employee.termination')
        vals.update({'ref': ref})
        return super(hr_employee_termination, self).create(vals)

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
        set department
        :return:
        """
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.saved_department_id = self.employee_id.department_id.id

    @api.multi
    def deactivate_user(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.user_id:
                rec.employee_id.user_id.active = False
            rec.write({'state': 'deactive_user'})

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'confirm':
            return 'hr_employee_state.mt_alert_state_confirm'
        elif 'state' in init_values and self.state == 'done':
            return 'hr_employee_state.mt_alert_state_done'
        elif 'state' in init_values and self.state == 'cancel':
            return 'hr_employee_state.mt_alert_state_cancel'
        return super(hr_employee_termination, self)._track_subtype(init_values)

    @api.multi
    def send_notify(self):
        '''
        This function opens a window to compose
         an email, with the edi sale
          template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'hr_employee_state', 'email_template_termination_emp')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'hr.employee.termination',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_message_type': 'email',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def _needaction_domain_get(self):
        users_obj = self.env['res.users']
        domain = []

        if users_obj.has_group('hr.group_hr_user'):
            domain = [('state', 'in', ['draft'])]

        if users_obj.has_group('hr.group_hr_manager'):
            if len(domain) > 0:
                domain = ['|'] + domain + [('state', '=', 'confirm')]
            else:
                domain = [('state', '=', 'confirm')]

        if len(domain) > 0:
            return domain

        return False

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('Unable to delete record! Employment '
                                  'termination already in progress. '
                                  'Use the "Cancel" button instead.'))

            # Trigger employee status change back to Active and contract back
            # to Open
            rec.employee_id.signal_active()
            for contract in rec.employee_id.contract_ids:
                if contract.state == 'close':
                    contract.write({'state': 'open'})
        return super(hr_employee_termination, self).unlink()

    @api.multi
    def effective_date_in_future(self):
        for rec in self:
            today = datetime.now().date()
            effective_date = datetime.strptime(
                rec.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    @api.multi
    def state_confirmed(self):
        for rec in self:
            exist_employee = self.search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', 'in', ['confirm', 'deactive_user', 'done'])])
            if exist_employee:
                raise UserError(_('This Employee %s already in progress %s '
                                  'state.') % (exist_employee.employee_id.name,
                                               exist_employee.state))
            if rec.employee_id:
                rec.employee_id.write({'status': 'pending_inactive'})
            rec.write({'state': 'confirm'})
        return True

    @api.multi
    def state_cancel(self):
        for rec in self:
            rec.employee_id.signal_active()
            for contract in rec.employee_id.contract_ids:
                contract.write({'state': 'open'})
            rec.write({'state': 'cancel'})
        return True

    @api.multi
    def state_done(self):
        for term in self:
            if term.employee_id:
                department_id = self.env['hr.department'].search([
                    ('manager_id', '=', term.employee_id.id)])
                employee_rec = self.env['hr.employee'].search([
                    ('parent_id', '=', term.employee_id.id)])
                if employee_rec or department_id:
                    raise UserError(
                        ('Please reassign the related dependancy'
                         ' for this employee before ending the request.'))
            if term.effective_date_in_future():
                raise UserError(('Unable to deactivate employee because '
                                 'effective date is still in the future'))
            if term.employee_id.contract_id:
                # contract.date_end = term.date
                term.employee_id.contract_id.with_context({
                    'termination': True,
                    'term_date': term.date}).state_close()
            term.employee_id.action_set_inactive()
            term.write({'state': 'done'})
        return True


class hr_job(models.Model):
    _inherit = 'hr.job'

    @api.depends('name', 'no_of_recruitment', 'employee_ids.job_id',
                 'employee_ids.active')
    def _compute_employees_new(self):
        # employee_data = self.env['hr.employee'].read_group([
        #     ('job_id', 'in', self.ids)], ['job_id'], ['job_id'])
        # result = dict((data['job_id'][0],
        #                data['job_id_count']) for data in employee_data)
        count = 0
        for job in self:
            for emp_rec in job.employee_ids:
                if emp_rec.active and emp_rec.status not in \
                        ['pending_inactive']:
                    count += 1

            job.no_of_employee = count
            job.expected_employees = \
                count + job.no_of_recruitment

    expected_employees = fields.Integer(compute='_compute_employees_new',
                                        store=True,
                                        string='Total Forecasted Employees',
                                        help='Expected number of employees '
                                             'for this job position after new '
                                             'recruitment.')
    no_of_employee = fields.Integer(compute='_compute_employees_new',
                                    store=True,
                                    string="Current Number of Employees",
                                    help='Number of employees currently '
                                         'occupying this job position.')


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    @api.multi
    def end_contract(self):

        # context.update({'end_contract_id': ids[0]})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.contract.end',
            'type': 'ir.actions.act_window',
            'target': 'new',
            # 'context': context
        }

    @api.multi
    def _state_common(self):

        # wkf = netsvc.LocalService('workflow')
        for contract in self:
            if contract.employee_id.status == 'new':
                contract.employee_id.status = 'onboarding'

    @api.multi
    def state_trial(self):
        """Override 'trial' contract state to also change employee state:
        new -> onboarding"""

        res = super(hr_contract, self).state_trial()
        self._state_common()
        return res

    @api.multi
    def state_open(self):
        """Override 'open' contract state to also change employee state:
         new -> onboarding"""

        res = super(hr_contract, self).state_open()
        self._state_common()
        return res

    @api.multi
    def try_signal_contract_completed(self):

        d = datetime.now().date()
        ids = self.search([
            ('state', '=', 'open'),
            ('date_end', '<', d.strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ])
        if len(ids) == 0:
            return

        for c in ids:
            vals = {
                'name': c.date_end and c.date_end or time.strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
                'employee_id': c.employee_id.id,
                'reason': 'contract_end',
            }
            self.setup_pending_done(vals)

        return

    @api.multi
    def setup_pending_done(self, term_vals):
        """Start employee deactivation process."""

        term_obj = self.env['hr.employee.termination']
        dToday = datetime.now().date()

        # If employee is already inactive simply end the contract

        if not self.employee_id.active:
            self.state_close()
            return

        # Ensure there are not other open contracts
        #
        open_contract = False
        for c2 in self.employee_id.contract_ids:
            if c2.id == self.id or c2.state == 'draft':
                continue

            if (not c2.date_end or datetime.strptime(c2.date_end,
                                                     DEFAULT_SERVER_DATE_FORMAT
                                                     ).date() >= dToday) \
                    and c2.state != 'close':
                open_contract = True

        # Don't create an employment termination if the employee has an open
        # contract or
        # if this contract is already in the 'done' state.
        if open_contract or self.state == 'close':
            return

        # Also skip creating an employment termination if there is already
        # one in
        # progress for this employee.
        #
        term_ids = term_obj.search([('employee_id', '=', self.employee_id.id),
                                    ('state', 'in', ['draft', 'confirm'])])
        if len(term_ids) > 0:
            return

        term_obj.create(term_vals)

        # Set the contract state to pending completion
        self.state_pending_done()
        # Set employee state to pending deactivation
        self.employee_id.state_pending_inactive()
