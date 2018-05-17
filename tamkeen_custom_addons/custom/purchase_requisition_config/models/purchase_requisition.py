# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime


class ResCompany(models.Model):
    _inherit = 'res.company'

    ceo_limit = fields. \
        Monetary(string='CEO validation amount',
                 default=1000000,
                 help="Minimum amount for which a CEO validation is required")
    budget_team_mail = fields.Char('Budget team mail')


class PurchaseConfigSetting(models.TransientModel):
    _inherit = 'purchase.config.settings'

    ceo_limit = fields. \
        Monetary(related='company_id.ceo_limit',
                 string='CEO validation amount',
                 help="Minimum amount for which a CEO validation is required",
                 currency_field='company_currency_id')


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    @api.multi
    def action_cancel(self):
        # try to set all associated quotations to cancel state
        for requisition in self:
            if requisition.purchase_ids:
                if any(purchase_order.state not in ['cancel'] for
                    purchase_order in self.mapped('purchase_ids')):
                    raise Warning(_('PR can not be cancelled'))
        self.write({'state':'cancel'})



    @api.model
    def default_get(self, fields):
        res = super(PurchaseRequisition, self).default_get(fields)
        if res.get('user_id'):
            res['user_id'] = False
        return res

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = window_action_ref = False
        if service_provider == 'purchase_requisition':
            window_action_ref = \
                'purchase_requisition.action_purchase_requisition'
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
        base_url = self.env['ir.config_parameter'].\
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
            'model': 'purchase.requisition'
        })
        return context

    @api.multi
    def _send_email(self, template_xml_ref, email_to, dest_state,
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
                    context.update(email_template_context)
                    template_rec.with_context(context).send_mail(
                        self.id, force_send=False)
            return True

    @api.multi
    @api.depends('est_cost', 'currency_id')
    def _get_estimated_cost(self):
        for rec in self:
            amount = rec.est_cost
            if rec.est_cost and rec.currency_id and rec.currency_id.id\
                    != self.env.user.company_id.currency_id.id:
                from_currency = rec.currency_id
                to_currency = self.env.user.company_id.currency_id
                amount = from_currency.compute(amount, to_currency, round=True)
            rec.estimated_cost = amount

    @api.model
    def _get_employee(self):
        employee_rec = self.env['hr.employee'] \
            .search([('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id

    @api.multi
    def _first_contract_date(self):
        # from many contract search for minimum contract date
        res = {}
        for payslip in self:
            date_list = []
            for contract in self.env['hr.contract'].search(
                    [('employee_id', '=', payslip.employee_ids.id)]):
                date_list.append(contract.date_start)
            if date_list:
                smallest_date = min(date_list)
                payslip.first_contract_date = smallest_date
                return res
        return False

    @api.multi
    def _get_po_name(self):
        for rec in self:
            po_name = ''
            rfq_name = ''
            for po in rec.purchase_ids:
                if po and po.po_company_number:
                    po_name += po.po_company_number + ','
                if po and po.name:
                    rfq_name += po.name + ','
            if po_name:
                rec.purchase_order_text = po_name[:-1]
            if rfq_name:
                rec.r_f_q_text = rfq_name[:-1]

    @api.multi
    def _get_po_initiated(self):
        for rec in self:
            po_initiated = False
            rfq_initiated = False
            for po in rec.purchase_ids:
                if po and po.po_company_number:
                    po_initiated = True
                if po and po.name:
                    rfq_initiated = True
            rec.po_initiated = po_initiated
            rec.rfq_initiated = rfq_initiated

    @api.multi
    def _bid_selection(self):
        for rec in self:
            rec.exclusive = 'multiple'

    name = fields.Char(string='Agreement Reference', required=True,
                       copy=False, default='New')
    estimated_cost =\
        fields.Float(compute='_get_estimated_cost',
                     string='Estimated Cost(Local Currency)', store=True)
    est_cost = fields.Float(string='Estimated Cost')
    other_details = fields.Text(string='Other Details')
    subject = fields.Text(string='Subject')
    contract_manager = fields. \
        Many2one('hr.employee', string='Contract Manager')
    budget = fields.Selection([
        ('under_budget', 'Under budget'),
        ('out_budget', 'Out of budget'),
        ('exceptional_out_budget', 'Out of Budget with Exception')
    ],
        string='Budget Status')
    budget_exception_reason = fields.Text(string='Budget Exception Reason')
    currency_id = fields. \
        Many2one('res.currency',
                 string='Currency',
                 default=lambda self:
                 self.env.user.company_id.currency_id.id,
                 required=True, readonly=True,
                 states={'draft': [('readonly', False)]})
    conversion_factor =\
        fields.Float(related='currency_id.rate',
                     string='Conversion Factor', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('tomanager_app', 'Manager Approval'),
        ('procurement_review', 'Procurement Review'),
        ('vp', 'VP approval'),
        ('budget', 'Budget Approval'),
        ('ceo', 'CEO Approval'),
        ('purchase_app', 'Purchase approval'),
        ('in_progress', 'Confirmed'),
        ('open', 'Bid Selection'),
        ('done', 'Closed Out'),
        ('cancel', 'Cancelled')],
        string='Status', track_visibility='onchange', required=True)

    exclusive = fields.Selection([('multiple', 'Select Multiple Bidders')],
                                 # compute=_bid_selection,
                                 default='multiple',
                                 string='Bid Selection Type',
                                 required=True,
                                 help="Select only one RFQ (exclusive):"
                                      "  On the confirmation of a "
                                      "purchase order, it cancels the"
                                      " remaining purchase order."
                                      "\nSelect multiple RFQ:"
                                      " It allows to have"
                                      " multiple purchase "
                                      "orders.On confirmation"
                                      " of a purchase order it"
                                      " does not cancel "
                                      "the remaining orders""")

    employee_ids = fields. \
        Many2one('hr.employee',
                 string="Requester",
                 readonly=False, default=_get_employee, copy=False)
    purchase_order_text =\
        fields.Char(compute='_get_po_name', string='Purchase Order')
    r_f_q_text = fields.Char(compute='_get_po_name', string='RFQ')
    rfq_initiated = fields.\
        Boolean(compute='_get_po_initiated', string='RFQ Initiated')
    rfq_initiated_store = fields. \
        Boolean(related='rfq_initiated', string='RFQ Initiated', store=True)
    po_initiated = fields.\
        Boolean(compute='_get_po_initiated', string='PO Initiated')
    po_initiated_store = fields. \
        Boolean(related='po_initiated', string='PO Initiated', store=True)
    # remarks = fields.Text(string='Remarks')

    mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                   readonly=True, copy=False)
    vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                 readonly=True,
                                 copy=False)
    pr_review_user_id = fields.Many2one('res.users', string='PR Review By',
                                        readonly=True,
                                        copy=False)
    finance_user_id = fields.Many2one('res.users', string='Finance Approval',
                                      readonly=True, copy=False)
    procurement_user_id = fields.Many2one('res.users', string='Procurement '
                                                              'Approval',
                                          readonly=True, copy=False)
    ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                  readonly=True,
                                  copy=False)
    pr_confirm_user_id = fields.Many2one('res.users', string='Confirmed User',
                                         readonly=True,
                                         copy=False)
    mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                         readonly=True, copy=False)
    vp_approval_date = fields.Datetime(string='VP Approval Date',
                                       readonly=True,
                                       copy=False)
    pr_review_date = fields.Datetime(string='PR Reviewing Date',
                                     readonly=True, copy=False)
    finance_approval_date = fields.Datetime(string='Finance Approval Date',
                                            readonly=True, copy=False)
    procurement_approval_date = fields.Datetime(
        string='Procurement Approval Date',
        readonly=True, copy=False)
    ceo_approval_date = fields.Datetime(string='CEO Approval Date',
                                        readonly=True,
                                        copy=False)
    pr_confirm_date = fields.Datetime(string='Purchase Confirm Date',
                                      readonly=True,
                                      copy=False)
    submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                  copy=False)
    submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        help='It will be automatically filled by the user who requested the '
             'service.')
    return_date = fields.Date(string='Return Date', readonly=True, copy=False)
    returned_by = fields.Many2one(
        'res.users',
        string='Returned By',
        readonly=True,
        help='It will be automatically filled by the last user who returned '
             'the service.',
        copy=False)
    is_office_change_mail = fields.Boolean('Notify Officer?')
    user_change = fields.Boolean('User change', invisible='1', default=False)

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            self.user_change = True

    @api.model
    def create(self, vals):
        if vals:
            seq = self.env['ir.sequence'].next_by_code(
                'purchase.order.requisition')
            vals.update({'name': seq})
            [line[2].update({'account_analytic_id':vals.get(
                'account_analytic_id', False)}) for line in vals.get(
                'line_ids')]
        res = super(PurchaseRequisition, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        for rec in self:
            res = super(PurchaseRequisition, self).write(vals)
            if vals.get('account_analytic_id', False):
                [x.write({'account_analytic_id':vals.get(
                    'account_analytic_id', False)})for x in rec.line_ids ]

            return res
    # @api.multi
    # def write(self, vals):
    #     if vals.get('is_office_change_mail'):
    #         template_obj = self.env['mail.template']
    #         ir_model_data = self.env['ir.model.data']
    #         for rec in self:
    #             try:
    #                 template_id = ir_model_data.get_object_reference(
    #                     'purchase_requisition_config',
    #                     'email_update_procurement_office')[
    #                     1]
    #             except ValueError:
    #                 template_id = False
    #             if template_id:
    #                 template_rec = template_obj.browse(template_id)
    #                 template_rec.send_mail(
    #                     rec.id, force_send=False)
    #         vals.update({'is_office_change_mail':
    #  False, 'user_change': False})
    #     return super(PurchaseRequisition, self).write(vals)

    @api.multi
    @api.constrains('estimated_cost')
    def _check_cost(self):
        for rec in self:
            if rec.estimated_cost <= 0:
                raise UserError(_("It's not allowed to raise a request"
                                  " with an estimated not grater than 0."))

    @api.multi
    def check_line_ids(self):
        for pr in self:
            if not pr.line_ids:
                raise Warning(_('You cannot send'
                                ' Purchase Requisition'
                                ' without Product/Service'))
        return True

    @api.multi
    def check_attachment(self):
        ir_obj = self.env['ir.attachment']
        for pr in self:
            attachment_rec = ir_obj.search([('res_id', '=', pr.id),
                                            ('res_model', '=',
                                             'purchase.requisition')])
            if len(attachment_rec) < 1:
                raise Warning(_('You cannot submit the request to the manager '
                                'without attaching a document. Kindly, save '
                                'the Procurement Requisition and attach a '
                                'document.'))
        return True

    @api.multi
    def _check_purch_ids(self):
        for pr in self:
            if not pr.purchase_ids:
                raise Warning(_('You cannot confirm'
                                ' Purchase Requisition without Quotation'))

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.type_id.mngr_approval:
                req_approvals.append('tomanager_app')
            if service.type_id.pr_review_approval:
                req_approvals.append('procurement_review')
            if service.type_id.vp_approval:
                req_approvals.append('vp')
            if service.type_id.budget_approval:
                req_approvals.append('budget')
            if service.est_cost >= self.env.user.company_id.ceo_limit:
                if service.type_id.ceo_approval:
                    req_approvals.append('ceo')
            if service.type_id.purchase_approval:
                req_approvals.append('purchase_app')
            if service.type_id.pr_confirm:
                req_approvals.append('in_progress')
        return req_approvals

    @api.multi
    def is_transition_allowed(self, wkf_state_signal):
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for service in self:
                if wkf_state_signal in req_approvals or wkf_state_signal == \
                        'accepted':
                    return True
        return False

    @api.multi
    def _get_dest_state(self, service):
        dest_state = ''
        current_state = service.state
        service_states = ['draft']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
        # service_states.append('refused') # to add the refused state
        # service_states.append('approved')  # to add the approved state
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    def _get_approval_info(self, service, dest_state):
        current_state = service.state
        # stage_id = self._get_related_stage_id(service, dest_state)
        # if not stage_id:
        #     raise Warning(_(
        #         "Stage ID not found, Please Configure Service Stages for "
        #         "%s") % (dest_state))
        # result = {'stage_id': stage_id.id}
        result = {}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'submitted_by': self.env.user.id,
                           'submit_date': self._get_current_datetime()})
        if current_state == 'tomanager_app':
            result.update(
                {'state': dest_state, 'mngr_user_id': self.env.user.id,
                 'mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp':
            result.update({'state': dest_state, 'vp_user_id': self.env.user.id,
                           'vp_approval_date': self._get_current_datetime()})
        if current_state == 'procurement_review':
            result.update({'state': dest_state,
                           'pr_review_user_id': self.env.user.id,
                           'pr_review_date': self._get_current_datetime()})
        if current_state == 'budget':
            result.update(
                {'state': dest_state, 'finance_user_id': self.env.user.id,
                 'finance_approval_date': self._get_current_datetime()})
        if current_state == 'purchase_app':
            result.update(
                {'state': dest_state, 'procurement_user_id': self.env.user.id,
                 'procurement_approval_date': self._get_current_datetime()})
        if current_state == 'ceo':
            result.update(
                {'state': dest_state, 'ceo_user_id': self.env.user.id,
                 'ceo_approval_date': self._get_current_datetime()})
        if current_state == 'in_progress':
            result.update(
                {'state': dest_state, 'pr_confirm_user_id': self.env.user.id,
                 'pr_confirm_date': self._get_current_datetime()})
        return result

    # All Button Comman method
    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have to check and run this code
        :return:
        """
        if self.is_transition_allowed('vp_approval'):
            self.service_validate1()
        elif self.is_transition_allowed('oe_approval'):
            self.service_validate2()
        elif self.is_transition_allowed('ta_approval'):
            self.service_validate3()
        elif self.is_transition_allowed('hr_approval'):
            self.service_validate4()
        elif self.is_transition_allowed('finance_approval'):
            self.service_validate5()
        elif self.is_transition_allowed('procurement_approval'):
            self.service_validate6()
        elif self.is_transition_allowed('ss_vp_approval'):
            self.service_validate7()
        elif self.is_transition_allowed('ceo_approval'):
            self.service_validate8()
        else:
            return False
        return True

    @api.multi
    def service_submit_mngr(self):
        for service in self:
            # self._check_user_permissions('approve')
            # self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                service.write(
                    self._get_approval_info(service,
                                            dest_state))
                service._send_email(
                    'purchase_requisition_config.email'
                    '_template_pr_update_manager',
                    None, dest_state, 'purchase_requisition')
                return True
            else:
                service.write({'state': 'tomanager_app'})

    @api.multi
    def to_manager(self):
        for rec in self:
            rec.check_line_ids()
            rec.check_attachment()
            if rec.is_transition_allowed('tomanager_app'):
                rec.service_submit_mngr()
            else:
                rec.write({'state': 'tomanager_app'})
            # else:
            #     rec._check_point_for_all_stage()
            # rec.write({'state': 'tomanager_app'})

    @api.multi
    def check_validate(self):
        '''
        Check current user is not approve purchase requsition.
        :return:
        '''
        for request in self:
            if not self.env.user.has_group('purchase_requisition_config.'
                                           'group_ceo_approval_pr')\
                    and request.user_id.id == self.env.user.id:
                raise Warning(_('You cannot approve'
                                ' your own purchase requisition'
                                ' \nEmployee: %s') %
                              (request.employee_ids.name))

    @api.multi
    def procurement_review(self):
        for rec in self:
            dest_state = self._get_dest_state(rec)
            if dest_state:
                rec.write(
                    self._get_approval_info(rec,
                                            dest_state))
                rec._send_email(
                    'purchase_requisition_config.email_template_manager_to_vp',
                    None, dest_state, 'purchase_requisition')
                return True
            else:
                rec.write({'state': 'vp'})

    @api.multi
    def to_vp(self):
        for rec in self:
            dest_state = self._get_dest_state(rec)
            if dest_state:
                rec.write(
                    self._get_approval_info(rec,
                                            dest_state))
                rec._send_email(
                    'purchase_requisition_config.email_'
                    'template_vp_to_budget_team',
                    None, dest_state, 'purchase_requisition')
                return True
            else:
                # rec.write({'state': 'budget'})
                rec.write({'state': 'budget'})

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default.update({'budget': False, 'user_id': False})
        return super(PurchaseRequisition, self).copy(default)

    @api.multi
    def manager_appr(self):
        for rec in self:
            rec.check_validate()
            dest_state = self._get_dest_state(rec)
            if dest_state == 'vp':
                rec.write(self._get_approval_info(rec, dest_state))
                s_em = 'purchase_requisition_config.' \
                       'email_template_review_purchase_requisition'
                rec._send_email(s_em, None, dest_state, 'purchase_requisition')
                return True
            else:
                # rec.write({'state': 'budget'})
                pr_em = \
                    'purchase_requisition_config.email_template_review_purchase_requisition'
                rec.write({'state': 'procurement_review'})
                rec._send_email(pr_em, None, dest_state, 'purchase_requisition')

    @api.multi
    def check_for_ref_validate(self):
        for this in self:
            if not self.env.user.has_group('purchase_requisition_config.'
                                           'group_ceo_approval_pr') \
                    and this.state == 'tomanager_app' \
                    and this.user_id.id == self.env.user.id:
                raise Warning(_('You cannot return your own request'))

    @api.multi
    def budget_appr(self):
        ceo_validation_amount \
            = self.env.user.company_id.ceo_limit
        for rec in self:
            if rec.budget:
                if rec.budget == 'out_budget':
                    raise Warning(_("You cannot"
                                    " proceed with this"
                                    " request because it's"
                                    " out of budget. "))
            else:
                raise Warning(
                    _("You cannot proceed without budget status. "))
            dest_state = self._get_dest_state(rec)
            if dest_state:
                rec.write(
                    self._get_approval_info(rec,
                                            dest_state))
                if dest_state == 'ceo':
                    rec._send_email(
                        'purchase_requisition_config.'
                        'email_template_budget_team_ceo',
                        None, dest_state, 'purchase_requisition')
                elif dest_state == 'purchase_app':
                    rec._send_email('purchase_requisition_config.'
                                    'email_template_budget_team_'
                                    'to_purchase_approval',
                                    None, dest_state, 'purchase_requisition')
            elif rec.estimated_cost >= ceo_validation_amount:
                rec.write({'state': 'ceo'})
            elif rec.estimated_cost <= ceo_validation_amount:
                rec.write({'state': 'purchase_app'})

    @api.multi
    def to_ceo(self):
        for rec in self:
            dest_state = self._get_dest_state(rec)
            if dest_state:
                rec.write(
                    self._get_approval_info(rec,
                                            dest_state))
                rec._send_email('purchase_requisition_config.'
                                'email_template_ceo_to_purchase_approval',
                                None, dest_state, 'purchase_requisition')
            else:
                rec.write({'state': 'purchase_app'})

    @api.multi
    def action_in_progress(self):
        for rec in self:
            rec._check_purch_ids()
            dest_state = self._get_dest_state(rec)
            if dest_state:
                rec.write(
                    self._get_approval_info(rec,
                                            dest_state))
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_purchase_approval_to_confirm',
                    None, dest_state, 'purchase_requisition')
                return True
            else:
                rec.write({'state': 'in_progress'})

    @api.multi
    def to_draft_state(self):
        for rec in self:
            rec.check_for_ref_validate()
            if rec.state == 'tomanager_app':
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_first_level_pr_return',
                    None, 'draft', 'purchase_requisition')
            if rec.state == 'vp':
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_from_vp_level_pr_return',
                    None, 'draft', 'purchase_requisition')
            if rec.state == 'budget':
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_from_budget_approval_level_to_pr_return',
                    None, 'draft', 'purchase_requisition')
            if rec.state == 'purchase_app':
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_from_purchase_level_pr_return',
                    None, 'draft', 'purchase_requisition')
            if rec.state == 'procurement_review':
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_from_procurement_level_pr_return',
                    None, 'draft', 'purchase_requisition')
            if rec.state == 'ceo':
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_from_ceo_level_to_pr_return',
                    None, 'draft', 'purchase_requisition')
            if rec.state == 'in_progress':
                rec._send_email(
                    'purchase_requisition_config.'
                    'email_template_confirm_to_return',
                    None, 'draft', 'purchase_requisition')
            rec.write({'state': 'draft',
                       'returned_by': self.env.user.id,
                       'return_date': self._get_current_datetime(), })
        return True

    @api.multi
    def forward_officer(self):
        '''
        This function opens a window to compose
         an email, with the edi sale
          template message loaded by default
        '''

        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id =\
                ir_model_data.get_object_reference(
                    'purchase_requisition_config',
                    'email_update_procurement_office')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.requisition',
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
                'purchase_requisition_config', 'email_template_edi_pr')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.requisition',
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

    @api.multi
    def generate_po(self, selected_po_ids):
        """
        Generate all purchase order based on
         selected lines, should only be
          called on one tender at a time
        """
        if not selected_po_ids:
            raise Warning(_('Warning! \n'
                            'You cannot confirm Purchase Requisition without '
                            'Quotation'))
        # check selected PO confirmed or not
        for po_rec in self.purchase_ids:
            if po_rec.id in selected_po_ids:
                if any(purchase_order.state in ['draft', 'sent', 'to approve']
                       for purchase_order in po_rec):
                    raise Warning(_('Warning! \n'
                                    'You have to cancel orvalidate every '
                                    'selected RfQ before closing the '
                                    'purchase requisition.'))
        # cancle remaining PO
        for po_rec in self.purchase_ids:
            if po_rec.id not in selected_po_ids:
                po_rec.button_cancel()
        # action done
        self.action_done()
        return True


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    description = fields.Text(string='Description')

    @api.model
    def create(self, vals):
        if vals:
            if vals.get('requisition_id'):
                req_rec = self.env['purchase.requisition'].browse(vals.get('requisition_id'))
                if req_rec:
                    vals.update({
                        'account_analytic_id':req_rec.account_analytic_id.id})
        res = super(PurchaseRequisitionLine, self).create(vals)
        return res


    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(PurchaseRequisitionLine, self)._onchange_product_id()
        if self.product_id:
            code = ''
            if self.product_id.default_code:
                code = '[' + self.product_id.default_code.encode('utf8') + ']'
            self.description = code + self.product_id.name.encode('utf8')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        super(PurchaseOrder, self)._onchange_requisition_id()
        if not self.requisition_id:
            return
        count = 1
        requisition_line_ids = []
        self.partner_ref = ''
        for order_line in self.order_line:
            for line in self.requisition_id.line_ids:
                # Update PO line
                if order_line.product_id.id \
                        == line.product_id.id and line.id \
                        not in requisition_line_ids:
                    order_line.name = line.description
                    order_line.price_unit = line.price_unit
                    order_line.sn_number = count
                    count += 1
                    requisition_line_ids.append(line.id)
                    break

    buyer_name = fields.Many2one(related='requisition_id.user_id',
                                 relation='res.users',
                                 string="Buyer's name")


class PurchaseRequisitionType(models.Model):

    _inherit = 'purchase.requisition.type'

    mngr_approval = fields.Boolean('Manager Approval')
    vp_approval = fields.Boolean('VP Approval')
    pr_review_approval = fields.Boolean('Procurement Review Approval')
    budget_approval = fields.Boolean('Budget Approval')
    ceo_approval = fields.Boolean('CEO Approval')
    finance_approval = fields.Boolean('Finance Approval')
    purchase_approval = fields.Boolean('Purchase Approval')

    pr_confirm = fields.Boolean('PR Confirm')
    purchase_bud_confirm = fields.Boolean('Budget Confirm')
    po_confirm = fields.Boolean('PO Confirm')
    vendor_bill_first = fields.Boolean('First Level')

    @api.onchange('budget_approval')
    def onchange_budget_approval(self):
        if self and self.budget_approval:
            self.purchase_bud_confirm = True
        elif self and self.budget_approval is False:
            self.purchase_bud_confirm = False

    # ta_approval = fields.Boolean('Talent Acquisition Approval')
    # hr_approval = fields.Boolean('HR Approval')
    # infrastructure_approval = fields.Boolean('Infrastructure Approva######l')
    # ss_vp_approval = fields.Boolean('Shared Services VP Approval')
    # procurement_approval = fields.Boolean('Procurement Approval')
    # administration_approval = fields.Boolean('Administration Approval')
