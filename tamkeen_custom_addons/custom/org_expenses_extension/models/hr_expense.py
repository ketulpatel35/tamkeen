from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError
from datetime import datetime, date
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from dateutil.relativedelta import relativedelta

import odoo.addons.decimal_precision as dp

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

SERVICE_STATUS = [('submit', 'To Submit'),
                  ('mngr_approval', 'Manager Approval'),
                  ('vp_approval', 'VP Approval'),
                  ('hr_approval', 'HR Approval'),
                  ('budget_approval', 'Budget Approval'),
                  ('ceo_approval', 'CEO Approval'),
                  ('approve', 'Approved'),
                  ('post', 'Finance Processing'),
                  ('rejected', 'Rejected'),
                  ('closed', 'Closed'),
                  ('cancel', 'Cancelled'),
                  # ('locked', 'Locked'),
                  # ('submit', 'Submitted'),
                  # ('approve', 'Approved'),
                  # ('post', 'Posted'),
                  ('done', 'Paid'),
                  ]



class HrExpense(models.Model):
    _inherit = "hr.expense.sheet"
    _description = "Expense Request"


    @api.multi
    def _get_employee_name(self):
        employee_rec = self.env['hr.employee'] \
            .search([('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    def _get_current_date(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.depends('expense_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.expense_approval_policy_id.sla_period or False
            sla_period_unit = \
                rec.expense_approval_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.expense_submit_date:
                    expense_submit_date = datetime.strptime(rec.expense_submit_date,
                                                         OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        expense_submit_date + _intervalTypes[
                            sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('expense_final_approval_user_id')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.expense_submit_date:
                expense_submit_date = datetime.strptime(rec.expense_submit_date,
                                                     OE_DTFORMAT)
                if rec.expense_final_approval_date:
                    expense_final_approval_date = datetime.strptime(
                        rec.expense_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(expense_final_approval_date,
                                         expense_submit_date)
                elif rec.state not in ['draft', 'refused', 'approve']:
                    diff = relativedelta(now, expense_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.expense_waiting_time = waiting_time

    name = fields.Char(string='Expense Report Summary', required=False, default=lambda self:
              self.env['ir.sequence'].next_by_code('hr.expense.sheet') or False)
    employee_id = fields.Many2one('hr.employee', 'Employee Name',
                                  default=_get_employee_name)
    expense_approval_policy_id = fields.Many2one(
        'service.configuration.panel', string='Expense Type',
        states={'draft': [('required', True)]})
    stage_id = fields.Many2one(
        'service.panel.displayed.states',
        string='States To Be Displayed',
        index=True,
        domain="[('service_type_ids', '=', expense_approval_policy_id)]",
        copy=False)
    state = fields.Selection(SERVICE_STATUS,
                             string='Status', readonly=True,
                             track_visibility='onchange',
                             default='submit')
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee ID')
    job_id = fields.Many2one(related='employee_id.job_id',
                             string='Position')
    department_id = fields.Many2one('hr.department',
                                    related='job_id.department_id',
                                    string='Organization Unit', store=True)
    org_unit_type_expe = fields.Selection([('root', 'Root'),
                                 ('business', 'Business Unit'),
                                 ('department', 'Department'),
                                ('section', 'Section')],
                                related='department_id.org_unit_type',
                                string='Organization Unit Type')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company')
    expense_summary = fields.Char('Expense summary')
    about_expense = fields.Text('About the Expense Type',
                                related='expense_approval_policy_id.about_service')
    endorsement_expense_required = fields.Boolean(string='Endorsement '
                                                         'Required',
                                               invisible=True)
    endorsement_expense_text = fields.Text(
        related='expense_approval_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True, copy=False)
    endorsement_expense_approved = fields.Boolean(string='Endorsement Approved',
                                               track_visibility='onchange',
                                               readonly=1, copy=False,
                                               states={'submit': [('readonly',
                                                                  False)]})
    expense_submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        help='It will be automatically filled by the user who requested the '
             'service.')
    expense_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                       copy=False)
    expense_waiting_time = fields.Char(compute=_calculate_ongoing_waiting_time,
                                    string='Waiting Time',
                                    method=True, copy=False,
                                    states={'submit': [('readonly', False)]})
    expense_final_approval_date = fields.Datetime('Final Approval Date',
                                               readonly=True, copy=False)
    expense_final_approval_user_id = fields.Many2one('res.users',
                                                  string='Final Approval',
                                                  readonly=True, copy=False)
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA',
        method=True,
        copy=False,
        states={
            'submit': [
                ('readonly',
                 False)]})
    expense_mngr_user_id = fields.Many2one('res.users', string='Manager '
                                                             'Approval',
                                        readonly=True, copy=False)
    expense_mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                              readonly=True, copy=False)
    expense_vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                      readonly=True, copy=False)
    expense_vp_approval_date = fields.Datetime(string='VP Approval Date',
                                            readonly=True, copy=False)
    expense_hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                      readonly=True, copy=False)
    expense_hr_approval_date = fields.Datetime(string='HR Approval Date',
                                            readonly=True, copy=False,
                                            track_visibility='onchange')
    expense_ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                       readonly=True, copy=False)
    expense_ceo_approval_date = fields.Datetime(string='CEO Approval Date',
                                             readonly=True, copy=False,
                                             track_visibility='onchange')
    expense_service_log_ids = fields.One2many('service.log',
                                           'expense_request_id',
                                           string='Service Logs')
    expense_rejected_user_id = fields.Many2one('res.users', string='Rejected '
                                                                  'By',
                                            readonly=True, copy=False)
    expense_rejected_date = fields.Datetime(string='Rejected Date',
                                         readonly=True, copy=False)
    payment_mode = fields.Selection(
        [("own_account", "Employee (to reimburse)"),
         ("company_account", "Company")],
        related='expense_line_ids.payment_mode', default='own_account',
        readonly=False, string="Payment By")

    @api.multi
    def _check_group(self, group_xml_id):
        user_rec = self.env.user
        if user_rec.has_group(str(group_xml_id)):
            return True
        return False

    def _get_expense_policy_id(self):
        if self.company_id and self.company_id.expense_policy_id:
            if self.company_id.expense_policy_id.valid_from_date and \
                    self.company_id.expense_policy_id.valid_to_date:
                today_date = datetime.today().date()
                from_date = datetime.strptime(
                    self.company_id.expense_policy_id.valid_from_date,
                    OE_DATEFORMAT).date()
                to_date = datetime.strptime(
                    self.company_id.expense_policy_id.valid_to_date,
                    OE_DATEFORMAT).date()
                if from_date <= today_date <= to_date:
                    return self.company_id.expense_policy_id
                else:
                    Warning(_('There is no an active policy for the expense'
                                ', For more information, Kindly '
                                'contact the HR Team.'))
            else:
                raise Warning(_('There is no an active policy for the expense'
                                ', For more information, Kindly '
                                'contact the HR Team.'))

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'hr_expense.action_hr_expense_sheet_all_to_approve'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    @api.multi
    def _set_email_template_context(self, data_pool,
                                    template_pool, email_to, dest_state,
                                    service_provider):
        context = dict(self._context)
        display_link = False
        base_url = self.env['ir.config_parameter']. \
            get_param('web.base.url.static')
        action_id = self._get_related_window_action_id(data_pool,
                                                       dest_state,
                                                       service_provider)
        if action_id:
            display_link = True
        context.update({
            'email_to': email_to,
            'base_url': base_url,
            'display_link': display_link,
            'action_id': action_id,
            'model': 'hr.expense.sheet'
        })
        return context

    @api.multi
    def _get_expense_related_stage_id(self, service, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        if dest_state == 'approve':
            dest_state = 'approved'
        if dest_state == 'post':
            dest_state = 'finance_processing'
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'hr.expense.sheet')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.multi
    def _send_email(self, template_xml_ref, email_to, dest_state, id,
                    service_provider):
        context = dict(self._context)
        if template_xml_ref:
            addon_name = template_xml_ref.split('.')[0]
            template_xml_id = template_xml_ref.split('.')[1]
            data_pool = self.env['ir.model.data']
            template_pool = self.env['mail.template']
            if self:
                # rec_id = ids[0]
                template_id = \
                    data_pool.get_object_reference(addon_name,
                                                   template_xml_id)[1]
                template_rec = template_pool.browse(template_id)
                if template_rec:
                    email_template_context = self._set_email_template_context(
                        data_pool, template_pool, email_to,
                        dest_state, service_provider)
                    if email_template_context:
                        context.update(email_template_context)
                    template_rec.with_context(context).send_mail(
                        id, force_send=False)
            return True

    @api.multi
    def check_dest_state_send_email(self, dest_state):
        context = dict(self._context)
        if dest_state == 'vp_approval':
            self._send_email(
                'org_expenses_extension.expense_pre_req_send_to_vp',
                None, dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'mngr_approval':
            self._send_email(
                'org_expenses_extension.expense_request_send_manager',None,
                dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'budget_approval':
            self._send_email(
                'org_expenses_extension.loan_pre_req_send_to_budget',
                None, dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'hr_approval':
            self._send_email(
                'org_expenses_extension.expense_pre_req_send_to_hr', None,
                dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'ceo_approval':
            self._send_email(
                'org_expenses_extension.expense_req_send_to_ceo', None,
                dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'approve':
            pass
            self._send_email(
                'org_expenses_extension.expense_req_approved', None,
                dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'rejected':
            self.with_context(context)._send_email(
                'org_expenses_extension.expense_req_rejected', None,
                dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'submit':
            self._send_email(
                'org_expenses_extension.email_template_loan_draft', None,
                dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'closed':
            self._send_email('org_expenses_extension.loan_req_closed', None,
                             dest_state, self.id, 'hr_expense_sheet')
        elif dest_state == 'finance_processing':
            self._send_email('org_expenses_extension.expensee_req_send_to_finance',
                             None, dest_state, self.id, 'hr_expense_sheet')

        return True

    @api.multi
    def _get_expense_dest_state(self, service):
        dest_state = ''
        current_state = service.state
        service_states = ['submit']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
        # service_states.append('refused') # to add the refused state
        service_states.append('finance_processing')  # to add the
        service_states.append('waiting_repayment')
        service_states.append('approve')
        # approved state'
        if current_state in service_states:
            current_state_index = service_states.index(current_state)
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    def _get_expense_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_expense_related_stage_id(service, dest_state)
        if not stage_id:
            raise Warning(_(
                "There is no related stage for  "
                "%s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'submit':
            result.update({'state': dest_state,
                           'expense_submitted_by': self.env.user.id,
                           'expense_submit_date': self._get_current_datetime()})
        if current_state == 'mngr_approval':
            result.update(
                {'state': dest_state, 'expense_mngr_user_id': self.env.user.id,
                 'expense_mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp_approval':
            result.update(
                {'state': dest_state, 'expense_vp_user_id': self.env.user.id,
                 'expense_vp_approval_date': self._get_current_datetime()})
        if current_state == 'budget_approval':
            result.update(
                {'state': dest_state})
        if current_state == 'hr_approval':
            result.update(
                {'state': dest_state, 'expense_hr_user_id': self.env.user.id,
                 'expense_hr_approval_date': self._get_current_datetime()})
        if current_state == 'ceo_approval':
            result.update(
                {'state': dest_state, 'expense_ceo_user_id': self.env.user.id,
                 'expense_ceo_approval_date': self._get_current_datetime()})
        if current_state == 'finance_processing':
            result.update(
                {'state': dest_state})
        if current_state == 'open':
            result.update(
                {'state': dest_state})
        if current_state == 'rejected':
            result.update(
                {'state': dest_state})
        if current_state == 'locked':
            result.update(
                {'state': dest_state})
        if current_state == 'waiting_repayment':
            result.update(
                {'state': dest_state})
        return result

    @api.onchange('company_id')
    def onchange_company_id(self):
        exp_request_id = self._get_expense_policy_id()
        # if not exp_request_id:
        #     raise Warning(_('You are not allowed to apply for this request '
        #                     'until the expense policy has been '
        #                     'applied.'))
        # if not self.expense_approval_policy_id:
        #     raise Warning(_('There is no an active policy for the expense, For more information, Kindly contact the HR Team.'))
        #     self.expense_approval_policy_id = exp_request_id.id
        if self.expense_approval_policy_id:
            self.onchange_expense_policy()

    @api.onchange('expense_approval_policy_id')
    def onchange_expense_policy(self):
        if self.expense_approval_policy_id:
            self.endorsement_expense_required = \
                self.expense_approval_policy_id.endorsement_required
            if self.expense_approval_policy_id.states_to_display_ids:
                for stage_rec in \
                        self.expense_approval_policy_id.states_to_display_ids:
                    if stage_rec.case_default:
                        self.stage_id = stage_rec.id
                        break
                    if not self.stage_id:
                        self.stage_id = \
                            self.expense_approval_policy_id.states_to_display_ids[
                                0].id

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.expense_approval_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.expense_approval_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.expense_approval_policy_id.budget_approval:
                req_approvals.append('budget_approval')
            if service.expense_approval_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.expense_approval_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
        return req_approvals

    @api.multi
    def action_submit_for_expense_approval(self):
        """
        method call from Button Submit for Approval
        :return:
        """
        # check condition
        # self.check_proofs()
        for rec in self:
            if not rec.expense_approval_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the loan policy has been applied.'))
            allow_behalf_req = self._check_group(
                'org_expenses_extension.group_expense_on_behalf_approval_srvs')
            if not allow_behalf_req:
                pass
                # employee_rec = self.env['hr.employee'] \
                #     .search([('user_id', '=', self._uid)], limit=1)
                # if self.employee_id != employee_rec:
                #     raise Warning(_('You are not allowed to do this change on '
                #                     'behalf of others.'))
        self._check_point_for_all_stage()

        # All Button Comman method

    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have t_get_loan_policy_ido check and run this code
        :return:
        """
        if self.is_transition_allowed('mngr_approval'):
            self.service_loan_submit_mngr()
        elif self.is_transition_allowed('vp_approval'):
            self.expense_service_validate1()
        elif self.is_transition_allowed('budget_approval'):
            self.expense_service_validate2()
        elif self.is_transition_allowed('hr_approval'):
            self.expense_service_validate3()
        elif self.is_transition_allowed('ceo_approval'):
            self.expense_service_validate4()
        else:
            return False
        return True

    @api.multi
    def service_loan_submit_mngr(self):
        for service in self:
            dest_state = self._get_expense_dest_state(service)
            self._check_expense_service_restrictions()
            if dest_state:
                self.write(
                    self._get_expense_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
                # self._send_email('hr_overtime.overtime_pre_req_send_manager')
                return True

    @api.multi
    def _check_user_permissions(self, signal='approve'):
        for rec in self:
            if not rec._check_group(
                    'org_expenses_extension.group_expense_self_approval_srvs'):
                if rec.state == 'mngr_approval' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(_("Please, Make sure that you have"
                                    " the rights to %s your own request.")
                                  % (signal))
        return False

    @api.multi
    def expense_service_validate1(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_expense_service_restrictions()
            dest_state = self._get_expense_dest_state(service)
            if dest_state:
                self.write(
                    self._get_expense_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def expense_service_validate2(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_expense_service_restrictions()
            dest_state = self._get_expense_dest_state(service)
            if dest_state:
                self.write(
                    self._get_expense_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def expense_service_validate3(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_expense_service_restrictions()
            dest_state = self._get_expense_dest_state(service)
            if dest_state:
                self.write(
                    self._get_expense_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def expense_service_validate4(self):
        for service in self:
            # check validation for hr approval
            self._check_user_permissions('approve')
            self._check_expense_service_restrictions()
            dest_state = self._get_expense_dest_state(service)
            # if dest_state == 'finance_processing':
                # final_approval = {
                #     'loan_final_approval_user_id': self.env.user.id,
                #     'expense_final_approval_date': self._get_current_datetime(),
                #     'open_user_id': self.env.user.id,
                #     'open_date': self._get_current_datetime(),
                #     'arrival_time_to_finance': self._get_current_datetime(),
                # }
                # self.write(final_approval)
            if dest_state:
                self.write(
                    self._get_expense_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def expense_service_validate5(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_expense_service_restrictions()
            dest_state = self._get_expense_dest_state(service)
            # final_approval = {
            #     'loan_final_approval_user_id': self.env.user.id,
            #     'expense_final_approval_date': self._get_current_datetime(),
            #     'open_user_id': self.env.user.id,
            #     'open_date': self._get_current_datetime(),
            #     'arrival_time_to_finance': self._get_current_datetime(),
            # }
            # self.write(final_approval)
            dest_state = 'approve'
            self.write(
                self._get_expense_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def action_sheet_move_create(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_expense_service_restrictions()
            dest_state = self._get_expense_dest_state(service)
            if any(sheet.state != 'approve' for sheet in self):
                raise UserError(_(
                    "You can only generate accounting entry for approved expense(s)."))

            if any(not sheet.journal_id for sheet in self):
                raise UserError(_(
                    "Expenses must have an expense journal specified to generate accounting entries."))

            res = self.mapped('expense_line_ids').action_move_create()

            if not self.accounting_date:
                self.accounting_date = self.account_move_id.date

            if self.payment_mode == 'own_account':
                self.write({'state': 'post'})
            else:
                self.write({'state': 'done'})
            dest_state = 'post'
            self.write(
                self._get_expense_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return res

    @api.multi
    def expense_service_validate6(self):
        context = dict(self._context)
        for service in self:
            self._check_user_permissions('approve')
            self._check_expense_service_restrictions()
            dest_state = 'rejected'
            self.write({'expense_rejected_user_id': self.env.user.id,
                        'expense_rejected_date':
                            self._get_current_datetime()})
            self.write(
                self._get_expense_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True


    def is_transition_allowed(self, wkf_state_signal):
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for service in self:
                if wkf_state_signal in req_approvals or wkf_state_signal == \
                        'accepted':
                    return True
        return False

    @api.multi
    def _check_expense_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.expense_approval_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise Warning(
                        _('You are not allowed to submit the request without '
                          'attaching a '
                          'document.\n For attaching a document: press save '
                          'then attach a document.'))
            if service.expense_approval_policy_id.endorsement_required and not \
                    service.endorsement_expense_approved:
                raise Warning(
                    _("To proceed, Kindly agree on the endorsement."))

    @api.multi
    def add_expense_line(self):
        # for rec in self:
        self.ensure_one()
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.expense',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_sheet_id': self.id,
                'default_employee_id': self.employee_id.id,
            }
        }




class ResCompany(models.Model):
    _inherit = 'res.company'

    expense_policy_id = fields.Many2one('service.configuration.panel',
                                     string='Default Expense Policy')


class ServiceLog(models.Model):
    _inherit = 'service.log'

    expense_request_id = fields.Many2one('hr.expense.sheet',
                                      string='Expense Request')


class ServiceLogWizard(models.TransientModel):
    _inherit = 'service.log.wizard'

    @api.multi
    def button_confirm(self):
        context = dict(self._context)
        service_log_rec = super(ServiceLogWizard, self).button_confirm()
        if service_log_rec and context.get('active_id') and context.get(
                'active_model'):
            active_model_obj = self.env[context.get('active_model', False)]
            active_id = context.get('active_id')
            active_rec = active_model_obj.browse(active_id)
            if str(context.get('active_model')) == 'hr.expense.sheet':
                service_log_rec.write(
                    {'expense_request_id': active_rec.id})
            if str(context.get('active_model')) == 'hr.expense.sheet':
                if context.get('trigger') and context.get('trigger') == 'Rejected':
                    active_rec.with_context({'reason': self.reason}).expense_service_validate6()
                if context.get('trigger') and context.get(
                        'trigger') == 'Locked':
                    active_rec.loan_service_validate7()
                if context.get('trigger') and context.get(
                        'trigger') == 'Returned':
                    active_rec.expense_service_validate10()
        return service_log_rec


class HrExpense(models.Model):

    _inherit = "hr.expense"

    product_id = fields.Many2one('product.product', string='Product',
                                 readonly=False,
                                 domain=[('can_be_expensed', '=', True)],
                                 required=True)
    unit_amount = fields.Float(string='Unit Price', readonly=False,
                               required=True,
                               states={'draft': [('readonly', False)],
                                       'refused': [('readonly', False)]},
                               digits=dp.get_precision('Product Price'))
    quantity = fields.Float(required=True, readonly=False,
                            states={'draft': [('readonly', False)],
                                    'refused': [('readonly', False)]},
                            digits=dp.get_precision('Product Unit of Measure'),
                            default=1)
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                                     required=True, readonly=False,
                                     states={'draft': [('readonly', False)],
                                             'refused': [('readonly', False)]},
                                     default=lambda self: self.env[
                                         'product.uom'].search([], limit=1,
                                                               order='id'))
    name = fields.Char(string='Expense Description', readonly=False,
                       required=False)

    @api.multi
    def create_expense_line(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}