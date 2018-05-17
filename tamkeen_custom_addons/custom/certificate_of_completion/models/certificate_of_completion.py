# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, date
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval)
}

SERVICE_STATUS = [('draft', 'To Submit'),
                  ('mngr_approval', 'Manager Approval'),
                  ('vp_approval', 'VP Approval'),
                  ('hr_approval', 'HR Approval'),
                  ('budget_approval', 'Budget Approval'),
                  ('procurement_first_review', 'Procurement First Review'),
                  ('business_owner_approval', 'Business Owner Approval'),
                  ('procurement_second_review', 'Procurement Second Review'),
                  ('pmo_approval', 'PMO Approval'),
                  ('finance_processing', 'Finance Processing'),
                  ('ceo_approval', 'CEO Approval'),
                  ('approved', 'Approved'),
                  ('rejected', 'Rejected'),
                  ('cancelled', 'Cancelled')]


class CertificateOfCompletion(models.Model):
    _name = "certificate.of.completion"
    _description = 'Certificate of Completion'
    _inherit = ['mail.thread']

    @api.depends('coc_po_order_line_ids')
    def compute_total_accepted_amount_qty(self):
        """
        compute total accepted amount
        :return:
        """
        for rec in self:
            total_accepted_amount = 0.0
            total_accepted_quantity = 0.0
            for line_rec in rec.coc_po_order_line_ids:
                total_accepted_amount += line_rec.accepted_amount
                total_accepted_quantity += line_rec.accepted_quantity
            rec.total_accepted_amount = total_accepted_amount
            rec.total_accepted_quantity = total_accepted_quantity

    @api.depends('line_ids')
    def compute_accepted_received_amount(self):
        """
        compute accepted_received_amount
        :return:
        """
        for rec in self:
            accepted_received_amount = 0.0
            for line_rec in rec.line_ids:
                accepted_received_amount += line_rec.accepted_amount
            rec.accepted_received_amount = accepted_received_amount

    @api.depends('total_accepted_quantity', 'total_accepted_amount',
                 'accepted_received_amount')
    def compute_accepted_received_quantity(self):
        """
        compute accepted received quantity
        :return:
        """
        for rec in self:
            if rec.total_accepted_quantity and \
                    rec.accepted_received_amount\
                    and rec.total_accepted_amount:
                rec.accepted_received_quantity = \
                    (rec.accepted_received_amount *
                     rec.total_accepted_quantity) / \
                    rec.total_accepted_amount

    @api.depends('coc_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        """
        SLA : calculate on going waiting time.
        :return:
        """
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.coc_submit_date:
                coc_submit_date = datetime.strptime(rec.coc_submit_date,
                                                    OE_DTFORMAT)
                if rec.coc_final_approval_date:
                    coc_final_approval_date = datetime.strptime(
                        rec.coc_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(coc_final_approval_date,
                                         coc_submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, coc_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.coc_waiting_time = waiting_time

    @api.depends('coc_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        """
        SLA : compute expected approval date as per SLA
        :return:
        """
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.coc_approval_policy_id.sla_period or False
            sla_period_unit = \
                rec.coc_approval_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.coc_submit_date:
                    coc_submit_date = datetime.strptime(rec.coc_submit_date,
                                                        OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        coc_submit_date + _intervalTypes[sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    name = fields.Char('Name')
    stage_id = fields.Many2one(
        'service.panel.displayed.states', string='States To Be Displayed',
        domain="[('service_type_ids', '=', coc_approval_policy_id)]",
        copy=False, index=True)
    state = fields.Selection(SERVICE_STATUS, string='Status', readonly=True,
                             track_visibility='onchange',
                             help='When the Coc is created the status is '
                                  '\'Draft\'.\n Then the request will be '
                                  'forwarded based on the service type '
                                  'configuration.',
                             default='draft')
    coc_approval_policy_id = fields.Many2one('service.configuration.panel',
                                             string='Policy')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  default=lambda self: self.env['hr.employee']
                                  .search([('user_id', '=', self._uid)],
                                          limit=1) or False)
    cost_center_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    date = fields.Date('Receiving Date', default=date.today())
    payment_term_id = fields.Many2one(
        'account.payment.term', related='purchase_order_id.payment_term_id',
        string='Payment Term')
    notes = fields.Text('Additional Terms')
    milestones_schedule_id = fields.Many2one('milestones.schedule',
                                             'Milestones Schedule')
    line_ids = fields.One2many('certificate.of.completion.line',
                               'certificate_of_completion_id', 'Deliverable')
    currency_id = fields.Many2one('res.currency',
                                  related='purchase_order_id.currency_id')
    company_id = fields.Many2one('res.company', 'Company',
                                 related='purchase_order_id.company_id')
    coc_po_order_line_ids = fields.One2many('coc.po.order.line',
                                            'certificate_of_completion_id',
                                            string='Order Line')
    accepted_received_amount = fields.Float(
        'Accepted Received Amount', compute='compute_accepted_received_amount',
        store=True)
    total_accepted_amount = fields.Float(
        'Total Accepted Amount', compute='compute_total_accepted_amount_qty',
        store=True)
    total_accepted_quantity = fields.Float(
        'Total Accepted Quantity', compute='compute_total_accepted_amount_qty',
        store=True)
    accepted_received_quantity = fields.Float(
        'Accepted Received Quantity',
        compute='compute_accepted_received_quantity', store=True)

    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        related='purchase_order_id.account_analytic_id')

    # service configuration fields
    submit_message = fields.Text(
        related='coc_approval_policy_id.submit_message',
        string='Submit Hint Message', store=True)
    endorsement_coc_required = fields.Boolean(
        related='coc_approval_policy_id.endorsement_required',
        string='Endorsement Required', invisible=True)
    endorsement_coc_text = fields.Text(
        related='coc_approval_policy_id.endorsement_text',
        string='Endorsement Text', readonly=True)
    endorsement_coc_approved = fields.Boolean(
        string='Endorsement Approved', track_visibility='onchange',
        readonly=1, states={'draft': [('readonly', False)]})
    # approvals fields
    coc_submitted_by = fields.Many2one('res.users', string='Submitted By',
                                       readonly=True, copy=False,
                                       help='It will be automatically filled '
                                            'by the user who requested the '
                                            'service.')
    coc_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                      copy=False)
    coc_mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                       readonly=True, copy=False)
    coc_mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                             readonly=True, copy=False)
    coc_vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                     readonly=True, copy=False)
    coc_vp_approval_date = fields.Datetime(string='VP Approval Date',
                                           readonly=True, copy=False)
    coc_budget_user_id = fields.Many2one('res.users', string='Budget Approval',
                                         readonly=True, copy=False)
    coc_budget_approval_date = fields.Datetime(string='Budget Approval Date',
                                               readonly=True, copy=False)
    coc_hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                     readonly=True, copy=False)
    coc_hr_approval_date = fields.Datetime(string='HR Approval Date',
                                           readonly=True, copy=False,
                                           track_visibility='onchange')
    coc_ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                      readonly=True, copy=False)
    coc_ceo_approval_date = fields.Datetime('CEO Approval Date',
                                            readonly=True, copy=False)
    procurement_first_user_id = fields.Many2one(
        'res.users', string='Procurement First Approval', readonly=True,
        copy=False)
    procurement_first_approval_date = fields.Datetime(
        'Procurement First Approval Date', readonly=True, copy=False)
    bus_owner_approval_user_id = fields.Many2one(
        'res.users', string='Business Owner Approval', readonly=True,
        copy=False)
    bus_owner_approval_date = fields.Datetime(
        'Business Owner Approval Date', readonly=True, copy=False)
    pmo_approval_user_id = fields.Many2one(
        'res.users', string='PMO Approval', readonly=True, copy=False)
    pmo_approval_date = fields.Datetime('PMO Approval Date', readonly=True,
                                        copy=False)
    procurement_second_user_id = fields.Many2one(
        'res.users', string='Procurement Second Approval', readonly=True,
        copy=False)
    procurement_second_approval_date = fields.Datetime(
        'Procurement Second Approval Date', readonly=True, copy=False)

    coc_final_approval_user_id = fields.Many2one('res.users',
                                                 string='Final Approval',
                                                 readonly=True, copy=False)
    coc_final_approval_date = fields.Datetime('Final Approval Date',
                                              readonly=True, copy=False)
    coc_return_user_id = fields.Many2one('res.users', string='Return By',
                                         readonly=True, copy=False)
    coc_return_date = fields.Datetime(string='Return Date',
                                      readonly=True, copy=False)
    coc_rejected_user_id = fields.Many2one('res.users', string='Rejected By',
                                           readonly=True, copy=False)
    coc_rejected_date = fields.Datetime(string='Rejected Date',
                                        readonly=True, copy=False)
    # SLA service
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA', method=True, copy=False,
        states={'draft': [('readonly', False)]})
    coc_waiting_time = fields.Char(
        compute=_calculate_ongoing_waiting_time, string='Waiting Time',
        method=True, states={'draft': [('readonly', False)]}, copy=False)
    # service log
    coc_service_log_ids = fields.One2many('service.log', 'coc_request_id',
                                          string='Service Logs')
    # service proof documents required
    proof_required = fields.Boolean(
        string='Proof Required',
        related='coc_approval_policy_id.proof_required', store=True)

    coc_proof_ids = fields.One2many(
        'certificate.of.completion.proof', 'certificate_of_completion_id')
    is_manual_coc = fields.Boolean('Create Manual Certificate of Completion')
    business_owner = fields.Many2one('res.users', 'Business Owner Name')

    @api.onchange('partner_id', 'cost_center_id')
    def onchange_partner_cost_center(self):
        """
        onchange of partner and cost center add domain of PO
        :return:
        """
        res = {}
        po_ids = []
        if self.is_manual_coc:
            self.purchase_order_id = False
            if self.partner_id or self.cost_center_id:
                domain = [
                    ('state', 'not in', ('draft', 'sent', 'to approve', 'bid',
                                         'budget_confirmed', 'cancel'))]
                if self.cost_center_id:
                    domain.append(
                        ('cost_centre_id', '=', self.cost_center_id.id))
                if self.partner_id:
                    domain.append(('partner_id', '=', self.partner_id.id))
                po_ids = self.env['purchase.order'].search(domain).ids
        return {'domain': {'purchase_order_id': [('id', 'in', po_ids)]}}

    @api.onchange('milestones_schedule_id')
    def onchange_milestones_schedule_id(self):
        """
        :return:
        """
        if self.milestones_schedule_id:
            # remove old records
            for line_rec in self.line_ids:
                self.line_ids = [(2, line_rec.id)]
            rem_amount, rem_per = self. \
                milestones_schedule_id.get_remaining_amount_percentage()
            self.line_ids = [{'name': self.milestones_schedule_id.id,
                              'rem_percentage': rem_per,
                              'rem_amount': rem_amount,
                              'vendor_percentage': 100,
                              'vendor_amount': rem_amount,
                              'accepted_percentage': 100,
                              'accepted_amount': rem_amount,
                              'make_it_as_final_line': True}]

    @api.onchange('coc_approval_policy_id')
    def onchange_coc_approval_policy_id(self):
        """
        set default stage
        :return:
        """
        if self.coc_approval_policy_id:
            if self.coc_approval_policy_id.states_to_display_ids:
                for display_state_rec in \
                        self.coc_approval_policy_id.states_to_display_ids:
                    if display_state_rec.case_default:
                        self.state_id = display_state_rec.id
                        break
                self.stage_id = \
                    self.coc_approval_policy_id.states_to_display_ids[0].id
            # proof required
            proof_lst = []
            if self.proof_required:
                self.coc_proof_ids.unlink()
                for line in self.coc_approval_policy_id.service_proof_ids:
                    proof_lst.append((0, 0, {'name': line.name, 'description':
                        line.description, 'mandatory': line.mandatory}))
            self.coc_proof_ids = proof_lst

    def _get_coc_policy_id(self):
        if self.company_id and self.company_id.coc_policy_id:
            return self.company_id.coc_policy_id

    @api.onchange('purchase_order_id')
    def onchange_purchase_order(self):
        """
        :return:
        """
        if self.purchase_order_id:
            pre_request_id = self._get_coc_policy_id()
            if not pre_request_id:
                raise ValidationError(
                    _('You are not allowed to apply for this request '
                      'until the Certificate of Completion policy is '
                      'applied.'))
            self.coc_approval_policy_id = pre_request_id.id
            for line_rec in self.line_ids:
                self.line_ids = [(2, line_rec.id)]
            line_data = []
            for line_rec in self.purchase_order_id.order_line:
                rem_qty = line_rec.product_qty - line_rec.qty_invoiced
                rem_amount = 0
                if rem_qty:
                    rem_amount = line_rec.price_unit * rem_qty
                line_data.append({
                    'po_order_line_id': line_rec.id,
                    'vendor_quantity': rem_qty,
                    'accepted_quantity': rem_qty,
                    'vendor_amount': rem_amount,
                    'accepted_amount': rem_amount
                })
            self.milestones_schedule_id = False
            self.coc_po_order_line_ids = line_data

    @api.model
    def create(self, vals):
        """
        :return:
        """
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'certificate.of.completion')
        res = super(CertificateOfCompletion, self).create(vals)
        return res

    @api.multi
    def update_done(self):
        """
        update milestone completion
        need to check letter
        :return:
        """
        for coc_rec in self:
            coc_rec.state = 'done'

    @api.multi
    def update_cancel(self):
        """
        update milestone completion
        need to check letter
        :return:
        """
        for coc_rec in self:
            coc_rec.state = 'cancel'

    def _prepare_invoice_line_from_coc_po_line(self, po_line_rec):
        if po_line_rec.product_id.purchase_method == 'purchase':
            qty = po_line_rec.product_qty - po_line_rec.qty_invoiced
        else:
            qty = po_line_rec.qty_received - po_line_rec.qty_invoiced
        if float_compare(
                qty, 0.0,
                precision_rounding=po_line_rec.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = po_line_rec.taxes_id
        invoice_line_tax_ids = \
            po_line_rec.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        cost_centre_id = po_line_rec.cost_centre_id and \
                         po_line_rec.cost_centre_id.id or False
        analytic_account = po_line_rec.account_analytic_id and \
                           po_line_rec.account_analytic_id.id or False
        name = po_line_rec.order_id.name + ': ' + po_line_rec.name
        data = {
            'purchase_line_id': po_line_rec.id,
            'name': name,
            'origin': po_line_rec.order_id.origin,
            'uom_id': po_line_rec.product_uom.id,
            'product_id': po_line_rec.product_id.id,
            # 'account_id': '',
            'price_unit': po_line_rec.order_id.currency_id.compute(
                po_line_rec.price_unit, po_line_rec.currency_id, round=False),
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': analytic_account,
            'analytic_tag_ids': po_line_rec.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            'r_quantity': True,
            'cost_centre_id': cost_centre_id,
            'date_invoice': date.today(),
        }
        account = invoice_line.get_invoice_line_account(
            'in_invoice', po_line_rec.product_id,
            po_line_rec.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

    @api.multi
    def coc_create_invoice(self):
        """
        create invoice from coc
        :return:
        """
        for rec in self:
            if not rec.invoice_id:
                account_analytic_id = rec.account_analytic_id and \
                                      rec.account_analytic_id.id or False
                cost_center_id = rec.cost_center_id and \
                                 rec.cost_center_id.id or False
                invoice_rec = self.env['account.invoice'].create({
                    'partner_id': rec.partner_id.id,
                    'cost_centre_id': cost_center_id,
                    'payment_term_id': rec.payment_term_id.id,
                    'account_analytic_id': account_analytic_id,
                    'origin': rec.purchase_order_id.name,
                    'currency_id': rec.currency_id.id,
                })
                # prepare invoice line
                for line_rec in rec.coc_po_order_line_ids:
                    data = self._prepare_invoice_line_from_coc_po_line(
                        line_rec.po_order_line_id)
                    data.update({'quantity': line_rec.accepted_quantity,
                                 'invoice_id': invoice_rec.id})
                    self.env['account.invoice.line'].create(data)
                rec.invoice_id = invoice_rec.id
                rec.coc_service_validate5()
                invoice_rec.certificate_of_completion_id = rec.id

    @api.constrains('total_accepted_amount', 'accepted_received_amount',
                    'accepted_received_quantity', 'total_accepted_quantity')
    def check_percentage_validation(self):
        """
        :return:
        """
        for rec in self:
            if rec.total_accepted_amount <= 0:
                raise ValidationError(_('Total Accepted Amount should not be zero!'))
            if int(rec.accepted_received_amount != rec.total_accepted_amount):
                raise ValidationError(_('Accepted Received Amount should be equal to '
                                'Total Accepted Amount!'))
            if round(rec.accepted_received_quantity, 2) != round(
                    rec.total_accepted_quantity, 2):
                raise ValidationError(_('Accepted Received Quantity should be equal '
                                'to Total Accepted Quantity!'))

    # buttons methods

    def _get_current_datetime(self):
        """
        return current datetime
        :return:
        """
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def _get_coc_dest_state(self, service):
        dest_state = ''
        current_state = service.state
        service_states = ['draft']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
        # service_states.append('refused') # to add the refused state
        service_states.append('approved')  # to add the approved state
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    @api.multi
    def _check_coc_group(self, group_xml_id):
        users_obj = self.env['res.users']
        if users_obj.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def _check_coc_user_permissions(self, signal='approve'):
        """
        user can approve/reject his own request
        :param signal:
        :return:
        """
        for rec in self:
            if not rec._check_coc_group(
                    'certificate_of_completion.group_coc_self_approval_srvs'):
                if rec.state == 'mngr_approval' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise ValidationError(
                        _("Please, Make sure that you have the rights to %s "
                          "your own request.") % (signal))
        return False

    @api.multi
    def _check_coc_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.coc_approval_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise ValidationError(
                        _('You cannot submit the request without attaching a '
                          'document.\n For attaching a document: press save '
                          'then attach a document.'))
            if service.coc_approval_policy_id.endorsement_required and not \
                    service.endorsement_coc_approved:
                raise ValidationError(
                    _("Please, You should agree on the endorsement to proceed "
                      "with your request."))

    @api.multi
    def _get_coc_related_stage_id(self, service, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'certificate.of.completion')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    def _get_coc_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_coc_related_stage_id(service, dest_state)
        if not stage_id:
            raise ValidationError(_(
                "Stage ID not found, Please Configure Service Stages for "
                "%s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'coc_submitted_by': self.env.user.id,
                           'coc_submit_date': self._get_current_datetime()})
        if current_state == 'mngr_approval':
            result.update(
                {'state': dest_state, 'coc_mngr_user_id': self.env.user.id,
                 'coc_mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp_approval':
            result.update(
                {'state': dest_state, 'coc_vp_user_id': self.env.user.id,
                 'coc_vp_approval_date': self._get_current_datetime()})
        if current_state == 'budget_approval':
            result.update(
                {'state': dest_state, 'coc_budget_user_id': self.env.user.id,
                 'coc_budget_approval_date': self._get_current_datetime()})
        if current_state == 'hr_approval':
            result.update(
                {'state': dest_state, 'coc_hr_user_id': self.env.user.id,
                 'coc_hr_approval_date': self._get_current_datetime()})
        if current_state == 'ceo_approval':
            result.update(
                {'state': dest_state, 'coc_ceo_user_id': self.env.user.id,
                 'coc_ceo_approval_date': self._get_current_datetime()})
        if current_state == 'procurement_first_review':
            result.update(
                {'state': dest_state,
                 'procurement_first_user_id': self.env.user.id,
                 'procurement_first_approval_date':
                     self._get_current_datetime()})
        if current_state == 'business_owner_approval':
            result.update({'state': dest_state,
                           'bus_owner_approval_user_id': self.env.user.id,
                           'bus_owner_approval_date':
                               self._get_current_datetime()})
        if current_state == 'procurement_second_review':
            result.update(
                {'state': dest_state,
                 'procurement_second_user_id': self.env.user.id,
                 'procurement_second_approval_date':
                     self._get_current_datetime()})
        if current_state == 'pmo_approval':
            result.update(
                {'state': dest_state,
                 'pmo_approval_user_id': self.env.user.id,
                 'pmo_approval_date':
                     self._get_current_datetime()})
        if current_state == 'finance_processing':
            result.update({'state': dest_state})
        if current_state == 'rejected':
            result.update({'state': dest_state})
        if current_state == 'locked':
            result.update({'state': dest_state})
        if current_state == 'cancelled':
            result.update({
                'state': dest_state,
                'cancel_date': self._get_current_datetime()})
        return result

    @api.multi
    def service_coc_submit_mngr(self):
        """
        submit for manager approval
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
                return True

    @api.multi
    def coc_service_validate1(self):
        """
        manager approved and submit for vp approval
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate2(self):
        """
        vp approved and submit for Procurement First Review
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate3(self):
        """
        HR approved and submit for budget approval
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate4(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate5(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'approved'
            final_approval = {
                'coc_final_approval_user_id': self.env.user.id,
                'coc_final_approval_date': self._get_current_datetime(),
            }
            self.write(final_approval)
            self.write(
                self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate6(self):
        """
        reject record
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'rejected'
            self.write({'coc_rejected_user_id': self.env.user.id,
                        'coc_rejected_date': self._get_current_datetime()})
            self.write(
                self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_forward_to_first_review(self):
        """
        procurement first reviewed and submit for Business Owner Approval
        :return:
        """
        ctx = self._context.copy()
        ctx.update({'first_approval': True, 'res_id': self.id})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'coc.forward.to.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
            'context': ctx,
        }

    @api.multi
    def coc_forward_to_second_review(self):
        """
        procurement first reviewed and submit for Business Owner Approval
        :return:
        """
        ctx = self._context.copy()
        ctx.update({'second_approval': True, 'res_id': self.id})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'coc.forward.to.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
            'context': ctx,
        }

    @api.multi
    def coc_service_validate7(self):
        """
        procurement first reviewed and submit for Business Owner Approval
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'business_owner_approval'
            self.write(
                self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate8(self):
        """
        Business Owner Approval and submit for Procurement Second Review
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'procurement_second_review'
            # self.write({'coc_rejected_user_id': self.env.user.id,
            #             'coc_rejected_date': self._get_current_datetime()})
            self.write(self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate9(self):
        """
        Procurement Second Reviewed and submit for PMO Approval
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'pmo_approval'
            # self.write({'coc_rejected_user_id': self.env.user.id,
            #             'coc_rejected_date': self._get_current_datetime()})
            self.write(self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate11(self):
        """
        financial processing after all approval.
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'finance_processing'
            # self.write({'coc_rejected_user_id': self.env.user.id,
            #             'coc_rejected_date': self._get_current_datetime()})
            self.write(self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate10(self):
        """
        returned record or set to draft
        :return:
        """
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'draft'
            self.write({
                'coc_submit_date': False,
                'coc_submitted_by': False,
                'coc_mngr_user_id': False,
                'coc_mngr_approval_date': False,
                'coc_vp_user_id': False,
                'coc_vp_approval_date': False,
                'coc_hr_user_id': False,
                'coc_hr_approval_date': False,
                'coc_budget_user_id': False,
                'coc_budget_approval_date': False,
                'coc_ceo_user_id': False,
                'coc_ceo_approval_date': False,
                'open_user_id': False,
                'open_date': False,
                'coc_closed_user_id': False,
                'coc_closed_date': False,
                'locked_user_id': False,
                'locked_date': False,
                'coc_rejected_user_id': False,
                'coc_rejected_date': False,
                'coc_cancel_user_id': False,
                'coc_cancel_date': False,
                'coc_expected_approval_date_as_sla': False,
                'coc_final_approval_date': False,
                'coc_final_approval_user_id': False,
                'coc_waiting_time': False,
                'bus_owner_approval_user_id': False,
                'bus_owner_approval_date': False,
                'procurement_first_user_id': False,
                'procurement_first_approval_date': False,
                'procurement_second_user_id': False,
                'procurement_second_approval_date': False,
                'pmo_approval_user_id': False,
                'pmo_approval_date': False,
                'business_owner': False,
            })
            self.write({'coc_return_user_id': self.env.user.id,
                        'coc_return_date': self._get_current_datetime()})
            self.write(
                self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.coc_approval_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.coc_approval_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            # if service.coc_approval_policy_id.budget_approval:
            #     req_approvals.append('budget_approval')
            # if service.coc_approval_policy_id.hr_approval:
            #     req_approvals.append('hr_approval')
            if service.coc_approval_policy_id.procurement_approval:
                req_approvals.append('procurement_first_review')
            if service.coc_approval_policy_id.business_owner_approval:
                req_approvals.append('business_owner_approval')
            if service.coc_approval_policy_id.procurement_second_review:
                req_approvals.append('procurement_second_review')
            if service.coc_approval_policy_id.pmo_approval:
                req_approvals.append('pmo_approval')
            if service.coc_approval_policy_id.finance_processing:
                req_approvals.append('finance_processing')
            if service.coc_approval_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
        return req_approvals

    def is_transition_allowed(self, wkf_state_signal):
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for service in self:
                if wkf_state_signal in req_approvals or wkf_state_signal == \
                        'accepted':
                    return True
        return False

    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have to check and run this code
        All button have common method
        :return:
        """
        if self.is_transition_allowed('mngr_approval'):
            self.service_coc_submit_mngr()
        elif self.is_transition_allowed('vp_approval'):
            self.coc_service_validate1()
        elif self.is_transition_allowed('budget_approval'):
            self.coc_service_validate2()
        elif self.is_transition_allowed('hr_approval'):
            self.coc_service_validate3()
        elif self.is_transition_allowed('ceo_approval'):
            self.coc_service_validate4()
        else:
            return False
        return True

    @api.multi
    def action_submit_for_coc_approval(self):
        """
        Submit for Approval button
        :return:
        """
        # check condition
        for rec in self:
            if not rec.coc_approval_policy_id:
                raise ValidationError(
                    _('You are not allowed to apply for this request '
                      'until the policy is applied.'))
        self._check_point_for_all_stage()

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'certificate_of_completion.certificate_of_completion_action_view'
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
            'model': 'certificate.of.completion'
        })
        return context

    @api.multi
    def _send_email(self, template_xml_ref, email_to, dest_state, id,
                    service_provider):
        """
        send email
        :param template_xml_ref: template xml id
        :param email_to: email to
        :param dest_state: destination state
        :param id: record id
        :param service_provider:
        :return:
        """
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
    def send_notify(self):
        """
        This function opens a window to compose an email, with the edi sale
        template message loaded by default
        :return:
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        # try:
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            # 'context': ctx,
        }

    @api.multi
    def check_dest_state_send_email(self, dest_state):
        """
        # send email based on destination stage
        :param dest_state: destination stage
        :return:
        """
        if dest_state == 'vp_approval':
            self._send_email(
                'certificate_of_completion.coc_pre_req_send_to_vp',
                None, dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'mngr_approval':
            self._send_email(
                'certificate_of_completion.coc_request_send_manager',
                None, dest_state, self.id, 'certificate_of_completion')
        # elif dest_state == 'budget_approval':
        #     self._send_email(
        #         'certificate_of_completion.coc_pre_req_send_to_budget',
        #         None, dest_state, self.id, 'certificate_of_completion')
        # elif dest_state == 'hr_approval':
        #     self._send_email(
        #         'certificate_of_completion.coc_pre_req_send_to_hr', None,
        #         dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'ceo_approval':
            self._send_email(
                'certificate_of_completion.coc_pre_req_send_to_ceo', None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'approved':
            self._send_email(
                'certificate_of_completion.coc_pre_req_approved', None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'rejected':
            self._send_email(
                'certificate_of_completion.email_template_coc_request_reject',
                None,
                dest_state, self.id, 'certificate_of_completion')
        # elif dest_state == 'cancelled':
        #     self._send_email(
        #         'certificate_of_completion.'
        #         'email_template_coc_request_cancelled', None,
        #         dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'draft':
            self._send_email(
                'certificate_of_completion.email_template_coc_request_draft',
                None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'procurement_first_review':
            self._send_email(
                'certificate_of_completion'
                '.coc_procurement_first_review_approval', None, dest_state,
                self.id, 'certificate_of_completion')
        elif dest_state == 'business_owner_approval':
            self._send_email(
                'certificate_of_completion.coc_business_owner_approval',
                None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'procurement_second_review':
            self._send_email(
                'certificate_of_completion'
                '.coc_procurement_second_review_approval', None, dest_state,
                self.id, 'certificate_of_completion')
        elif dest_state == 'pmo_approval':
            self._send_email(
                'certificate_of_completion'
                '.email_coc_pmo_approval', None, dest_state,
                self.id, 'certificate_of_completion')
        elif dest_state == 'finance_processing':
            self._send_email(
                'certificate_of_completion'
                '.email_coc_finance_processing', None, dest_state,
                self.id, 'certificate_of_completion')

        return True


class CertificateOfCompletionLine(models.Model):
    _name = "certificate.of.completion.line"
    _description = 'Certificate of Completion Line'

    name = fields.Many2one('milestones.schedule', 'Action')
    description = fields.Text('Remarks', related='name.description')
    rem_percentage = fields.Float('Percentage')
    rem_amount = fields.Float('Amount')
    vendor_percentage = fields.Float('Percentage Received from the Vendor')
    vendor_amount = fields.Float('Amount Received from the Vendor')
    accepted_percentage = fields.Float('Accepted Percentage')
    accepted_amount = fields.Float('Accepted Amount')
    justification = fields.Text('Justification')
    certificate_of_completion_id = fields.Many2one(
        'certificate.of.completion', 'Certificate of Completion')
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order',
        related='certificate_of_completion_id.purchase_order_id')
    make_it_as_final_line = fields.Boolean('Make It Final For this line Item')

    @api.constrains('vendor_percentage', 'accepted_percentage')
    def check_percentage_validation(self):
        """
        :return:
        """
        for rec in self:
            if rec.vendor_percentage < 1 or rec.vendor_percentage > 100:
                raise ValidationError(_('Received Vendor Percentage should be in '
                                'between 1 to 100 !'))
            if rec.accepted_percentage < 1 or rec.accepted_percentage > 100:
                raise ValidationError(_('Accepted Percentage should be in between 1 '
                                'to 100 !'))

    @api.onchange('vendor_percentage')
    def onchange_vendor_percentage(self):
        """
        onchange of percentage count amount.
        :return:
        """
        vendor_amount = 0.0
        if self.vendor_percentage and self.rem_amount:
            vendor_amount = (self.rem_amount * self.vendor_percentage) / 100
        self.vendor_amount = vendor_amount

    @api.onchange('vendor_amount')
    def onchange_vendor_amount(self):
        """
        onchange of amount calculate percentage
        :return:
        """
        vendor_percentage = 0.0
        if self.vendor_amount and self.rem_amount:
            vendor_percentage = (self.vendor_amount * 100) / self.rem_amount
        self.vendor_percentage = vendor_percentage

    @api.onchange('accepted_percentage')
    def onchange_accepted_percentage(self):
        """
        onchange of accepted amount count.
        :return:
        """
        accepted_amount = 0.0
        if self.accepted_percentage and self.rem_amount:
            accepted_amount = \
                (self.rem_amount * self.accepted_percentage) / 100
        self.accepted_amount = accepted_amount
        if self.accepted_percentage == 100:
            self.make_it_as_final_line = True
        else:
            self.make_it_as_final_line = False

    @api.onchange('accepted_amount')
    def onchange_accepted_amount(self):
        """
        onchange of amount calculate percentage
        :return:
        """
        accepted_percentage = 0.0
        if self.accepted_amount and self.rem_amount:
            accepted_percentage = \
                (self.accepted_amount * 100) / self.rem_amount
        self.accepted_percentage = accepted_percentage


class CocPoOrderLine(models.Model):
    _name = 'coc.po.order.line'

    @api.depends('product_qty', 'qty_invoiced')
    def compute_remaining_qty(self):
        """
        compute remaining quantity
        :return:
        """
        for rec in self:
            rec.remaining_qty = rec.product_qty - rec.qty_invoiced

    @api.depends('price_unit', 'remaining_qty')
    def compute_amount(self):
        for rec in self:
            if rec.remaining_qty and rec.price_unit:
                rec.amount = rec.remaining_qty * rec.price_unit

    certificate_of_completion_id = fields.Many2one(
        'certificate.of.completion', string='Certificate of Completion')
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order',
        related='certificate_of_completion_id.purchase_order_id')
    # po_order_line_id and its related fields
    po_order_line_id = fields.Many2one('purchase.order.line',
                                       string='Purchase Order Line')
    product_id = fields.Many2one('product.product', string='Product',
                                 related='po_order_line_id.product_id')
    product_uom = fields.Many2one('product.uom',
                                  string='Product Unit of Measure',
                                  related='po_order_line_id.product_uom')
    price_unit = fields.Float(string='Unit Price', required=True,
                              related='po_order_line_id.price_unit',
                              digits=dp.get_precision('Product Price'))
    product_qty = fields.Float(string='Quantity',
                               digits=dp.get_precision('Product Price'),
                               related='po_order_line_id.product_qty')
    qty_invoiced = fields.Float(related='po_order_line_id.qty_invoiced',
                                string="Billed Qty")
    remaining_qty = fields.Float('Remaining Quantity',
                                 digits=dp.get_precision('Product Price'),
                                 compute='compute_remaining_qty', store=True)
    amount = fields.Float('Amount', compute='compute_amount', store=True)
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        related='po_order_line_id.account_analytic_id')

    vendor_amount = fields.Float('Received Vendor Amount')
    vendor_quantity = fields.Float('Received Vendor Quantity',
                                   digits=dp.get_precision('Product Price'))
    accepted_amount = fields.Float('Accepted Amount')
    accepted_quantity = fields.Float('Accepted Quantity',
                                     digits=dp.get_precision('Product Price'))

    @api.onchange('vendor_quantity')
    def onchange_vendor_quantity(self):
        """
        onchange of vendor_quantity calculate amount
        :return:
        """
        if self._context and self._context.get('vendor_quantity'):
            if not self.vendor_quantity:
                self.vendor_amount = 0.0
            if self.price_unit and self.vendor_quantity:
                self.vendor_amount = self.price_unit * self.vendor_quantity

    @api.onchange('vendor_amount')
    def onchange_vendor_amount(self):
        """
        onchange of vendor_amount calculate vendor_quantity
        :return:
        """
        if self._context and self._context.get('vendor_amount'):
            if self.price_unit and self.vendor_amount and self.remaining_qty:
                self.vendor_quantity = \
                    (self.remaining_qty * self.vendor_amount) / self.amount

    @api.onchange('accepted_amount')
    def onchange_accepted_amount(self):
        """
        onchange of accepted_amount calculate accepted_quantity
        :return:
        """
        if self._context and self._context.get('accepted_amount'):
            if self.price_unit and self.accepted_amount and self.remaining_qty:
                self.accepted_quantity = \
                    (self.remaining_qty * self.accepted_amount) / self.amount

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price, currency, self.quantity, product=self.product_id,
                partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes[
            'total_excluded'] if taxes else self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.company_id and \
                        self.invoice_id.currency_id != \
                        self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(
                date=self.invoice_id.date_invoice).compute(
                price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    @api.onchange('accepted_quantity')
    def onchange_accepted_quantity(self):
        """
        onchange of accepted_quantity calculate accepted_amount
        :return:
        """
        if self._context and self._context.get('accepted_quantity'):
            if not self.accepted_quantity:
                self.accepted_amount = 0.0
            if self.price_unit and self.accepted_quantity:
                self.accepted_amount = self.price_unit * self.accepted_quantity
