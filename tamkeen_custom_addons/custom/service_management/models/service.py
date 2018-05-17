# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
from odoo import SUPERUSER_ID

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

SERVICE_STATUS = [('draft', 'To Submit'),
                  ('mngr_approval', 'Manager Approval'),
                  ('vp_approval', 'VP Approval'),
                  ('administration_approval', 'Administration Approval'),
                  ('oe_approval', 'OE Approval'),
                  ('ta_approval', 'TA Approval'),
                  ('hr_approval', 'HR Approval'),
                  ('finance_approval', 'Finance Approval'),
                  ('procurement_approval', 'Procurement Approval'),
                  ('ss_vp_approval', 'Shared Services VP Approval'),
                  ('ceo_approval', 'CEO Approval'),
                  ('approved', 'Approved'),
                  ('refused', 'Refused')]
SRVC_PRVDR = [('hr', 'HR'), ('administration', 'Administration'),
              ('recruitment', 'Recruitment')]

TEST_STATUS = [('draft', 'To Submit'),
               ('mngr_approval', 'Manager Approval'),
               ('vp_approval', 'VP Approval')]


class service_request(models.Model):
    _name = 'service.request'
    _description = 'Service Requests Management'
    _inherit = ['mail.thread']
    _order = 'submit_date desc, create_date desc'

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.submit_date:
                submit_date = datetime.strptime(rec.submit_date, OE_DTFORMAT)
                if rec.final_approval_date:
                    final_approval_date = datetime.strptime(
                        rec.final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(final_approval_date, submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.waiting_time = waiting_time

    @api.multi
    def _calculate_expected_approval_date_as_sla(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.service_type_id.sla_period or False
            sla_period_unit = rec.service_type_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.submit_date:
                    submit_date = datetime.strptime(rec.submit_date,
                                                    OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        submit_date + _intervalTypes[
                            sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.model
    def _select_objects(self):
        records = self.env['ir.model'].search([])
        return [(record.model, record.name) for record in records] + [('', '')]

    reference = fields.Char('Reference', size=64,
                            required=False, readonly=True,
                            default=lambda self:
                            self.env['ir.sequence'].next_by_code(
                                'service.request'))
    employee_id = fields.Many2one('hr.employee', "Employee",
                                  required=True,
                                  default=lambda self: self.
                                  env['hr.employee'].search(
                                      [('user_id', '=', self.env.user.id)],
                                      limit=1))

    f_employee_no = fields.Char(string='Employee Company ID')
    department_id = fields.Many2one('hr.department',
                                    string='Organization Unit',
                                    related='employee_id.department_id',
                                    store=True, readonly=True)
    service_type_id = fields.Many2one("service.type", "Service Type",
                                      required=True)
    service_provider = fields.Selection(
        SRVC_PRVDR, string='Service Provider', readonly=True, states={
            'draft': [
                ('readonly', False)]}, help="The responsible business "
                                            "unit "
                                            "for granting this service.")
    service_category_id = fields.Many2one('service.category',
                                          string='Service Category',
                                          store=True)
    about_service = fields.Text(
        string='About The Service',
        related='service_type_id.about_service',
        readonly=True,
        store=True)
    details = fields.Text('Details',
                          required=False)
    employee_id_view = fields.Many2one('hr.employee', string="Employee Name")
    state = fields.Selection(SERVICE_STATUS, 'Status', readonly=True,
                             track_visibility='onchange',
                             help='When the request is created the status is '
                                  '\'Draft\'.\n Then the request will be '
                                  'forwarded based on the service type '
                                  'configuration.',
                             default='draft')
    reference_id = fields.Reference(string='Reference',
                                    selection='_select_objects')
    # --- Approvals ---

    # first_user_id = fields.Many2one('res.users', 'First Approval',
    #                                 readonly=True,
    #                                 help='It will be automatically filled'
    #                                      ' by the user who validate the '
    #                                      'request as first level')
    # second_user_id = fields.Many2one('res.users', 'Second Approval',
    #                                  readonly=True,
    #                                  help='It will be automatically '
    #                                       'filled by the user who '
    #                                       'validate the request as '
    #                                       'second level.')
    # third_user_id = fields.Many2one('res.users', 'Third Approval',
    #                                 readonly=True,
    #                                 help='It will be automatically filled'
    #                                      ' by the user who validate the '
    #                                      'request as third level.')
    # fourth_user_id = fields.Many2one('res.users', 'Fourth Approval',
    #                                  readonly=True,
    #                                  help='It will be automatically '
    #                                       'filled by the user who validate '
    #                                       'the request as forth level.')
    # fifth_user_id = fields.Many2one('res.users', 'Fifth Approval',
    #                                 readonly=True,
    #                                 help='It will be automatically filled'
    #                                      'by the user who validate the '
    #                                      'request as fifth level.')
    # first_approval_date = fields.Datetime('First Approval Date',
    #                                       readonly=True)
    # second_approval_date = fields.Datetime('Second Approval Date',
    #                                        readonly=True)
    # third_approval_date = fields.Datetime('Third Approval Date',
    #                                       readonly=True)
    # fourth_approval_date = fields.Datetime('Fourth Approval Date',
    #                                        readonly=True)
    # fifth_approval_date = fields.Datetime('Fifth Approval Date',
    #                                       readonly=True)
    # request_date = fields.Date('Request Date',
    #                            required=True, readonly=True,
    #                            default=lambda *a:
    #                            time.strftime('%Y-%m-%d'), )
    # requested_by = fields.Many2one('res.users', 'Requested By',
    #                                readonly=True,
    #                                help='It will be automatically '
    #                                     'filled by the user '
    #                                     'who requested the service.',
    #                                default=lambda self: self.env.uid)

    mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                   readonly=True, copy=False)
    vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                 readonly=True,
                                 copy=False)
    adminis_user_id = fields.Many2one('res.users', string='Administration '
                                                          'Approval',
                                      readonly=True, copy=False)
    oe_user_id = fields.Many2one('res.users',
                                 string='Organization Effectiveness‬‏ '
                                        'Approval',
                                 readonly=True, copy=False)
    ta_user_id = fields.Many2one('res.users', string='Talent Acquisition '
                                                     'Approval',
                                 readonly=True, copy=False)
    hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                 readonly=True,
                                 copy=False)
    finance_user_id = fields.Many2one('res.users', string='Finance Approval',
                                      readonly=True, copy=False)
    procurement_user_id = fields.Many2one('res.users', string='Procurement '
                                                              'Approval',
                                          readonly=True, copy=False)
    ss_vp_user_id = fields.Many2one('res.users',
                                    string='Shared Services VP Approval',
                                    readonly=True, copy=False)
    ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                  readonly=True,
                                  copy=False)
    final_approval_user_id = fields.Many2one('res.users', string='Final '
                                                                 'Approval',
                                             readonly=True, copy=False)
    mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                         readonly=True, copy=False)
    vp_approval_date = fields.Datetime(string='VP Approval Date',
                                       readonly=True,
                                       copy=False)
    adminis_approval_date = fields.Datetime(string='Administration Approval '
                                                   'Date',
                                            readonly=True, copy=False)
    oe_approval_date = fields.Datetime(
        string='Organization Effectiveness‬‏ Approval Date', readonly=True)
    ta_approval_date = fields.Datetime(stirng='Talent Acquisition Approval '
                                              'Date',
                                       readonly=True, copy=False)
    hr_approval_date = fields.Datetime(string='HR Approval Date',
                                       readonly=True,
                                       copy=False)
    finance_approval_date = fields.Datetime(string='Finance Approval Date',
                                            readonly=True, copy=False)
    procurement_approval_date = fields.Datetime(
        string='Procurement Approval Date',
        readonly=True, copy=False)
    ss_vp_approval_date = fields.Datetime(string='Shared Services VP '
                                                 'Approval Date',
                                          readonly=True, copy=False)
    ceo_approval_date = fields.Datetime(string='CEO Approval Date',
                                        readonly=True,
                                        copy=False)
    final_approval_date = fields.Datetime('Final Approval Date',
                                          readonly=True, copy=False)
    submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                  copy=False)
    submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        help='It will be automatically filled by the user who requested the '
             'service.')

    refuse_date = fields.Date('Refuse Date', readonly=True)
    refused_by = fields.Many2one('res.users', 'Refused By',
                                 readonly=True,
                                 help='It will be automatically '
                                      'filled by the last user'
                                      ' who refused the service.')
    return_date = fields.Date(string='Return Date', readonly=True, copy=False)
    returned_by = fields.Many2one(
        'res.users',
        string='Returned By',
        readonly=True,
        help='It will be automatically filled by the last user who returned '
             'the service.',
        copy=False)
    ar_destination_required = fields.Boolean('Destination '
                                             'Required (AR)',
                                             invisible=True)
    en_destination_required = fields.Boolean('Destination '
                                             'Required (EN)',
                                             invisible=True)
    ar_destination = fields.Char('Destination (Arabic)',
                                 readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 size=500)
    en_destination = fields.Char('Destination (English)',
                                 readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 size=500)
    quantity_required = fields.Boolean('Quantity Required',
                                       invisible=True)
    priority_required = fields.Boolean('Priority Required',
                                       invisible=True)
    completion_date_required = fields.Boolean('Completion '
                                              'Date Required',
                                              invisible=True)
    details_required = fields.Boolean('Details Required',
                                      invisible=True)
    job_position_required = fields.Boolean(string='Job Position Required',
                                           invisible=True)
    endorsement_required = fields.Boolean(string='Endorsement Required',
                                          invisible=True)
    quantity = fields.Float(string='Quantity', readonly=True, states={
        'draft': [('readonly', False)]}, help="The number of items you need "
                                              "to request.")
    priority = fields.Selection([('critical', 'Critical'),
                                 ('high', 'High'),
                                 ('medium', 'Medium'),
                                 ('low', 'Low')],
                                string='Priority', readonly=True,
                                states={'draft': [('readonly', False)]})
    completion_date = fields.Date('Expected Completion Date',
                                  readonly=True,
                                  states={'draft': [('readonly', False)]})
    endorsement_text = fields.Text(related='service_type_id.endorsement_text',
                                   string='Endorsement Text',
                                   readonly=True)
    endorsement_approved = fields.Boolean(string='Endorsement Approved',
                                          track_visibility='onchange')
    job_id = fields.Many2one('hr.job', string='Position', readonly=True,
                             states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get())
    waiting_time = fields.Char(compute=_calculate_ongoing_waiting_time,
                               string='Waiting Time',
                               method=True, copy=False,
                               states={'draft': [('readonly', False)]})
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA',
        method=True,
        store=True,
        copy=False,
        states={
            'draft': [
                ('readonly',
                 False)]})
    stage_id = fields.Many2one(
        'service.displayed.states',
        string='States To Be Displayed',
        index=True,
        domain="[('service_type_ids', '=', service_type_id)]",
        copy=False)
    file_to_fill = fields.Binary(
        related='service_type_id.file_to_fill',
        string='File To Fill',
        help="The required template that should be filled by the requester.",
        readonly=True,
        copy=False,
        states={
            'draft': [
                ('readonly',
                 False)]},
        store=True)
    date_from_required = fields.Boolean(string='Date From Required',
                                        invisible=True)
    date_to_required = fields.Boolean(string='Date To Required',
                                      invisible=True)
    date_from = fields.Datetime(string='Date From', copy=False)
    date_to = fields.Datetime(string='Date To', copy=False)
    departure_from_required = fields.Boolean('Departure From Required')
    destination_required = fields.Boolean('Destination Required')
    departure_from = fields.Many2one('res.country.state','Departure From')
    destination = fields.Many2one('res.country.state', 'Destination')
    flight_option_required = fields.Boolean('Flight Option Required')
    flight_option = fields.Selection([('one_way', 'One Way'),
                                      ('round_trip', 'Round Trip')],
                                     string='Flight Option')
    refuse_reason = fields.Text(string='Refuse Reason')

    # general_service = fields.Boolean('General Service')
    # hr_service = fields.Boolean('HR Service')
    # infrastructure_service = fields.Boolean('Infrastructure '
    #                                         'Service')
    # administration_service = fields.Boolean('Administration Service')

    @api.model
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].next_by_code(
            'service.request')
        return super(service_request, self).create(vals)

    @api.multi
    def _check_group(self, group_xml_id):
        users_obj = self.env['res.users']
        if users_obj.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def copy(self, default=None):
        if not self._check_group(
                'service_management.group_service_on_behalf_approval_srvs'
        ):
            for rec in self:
                if rec.employee_id.user_id.id != self._uid:
                    raise Warning(_(
                        "You don't have the permissions to make such changes."
                    ))
        return super(service_request, self).copy(default=default)

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            display_name = record.service_type_id.name + ' Service Request'
            res.append((record.id, display_name.title()))
        return res

    @api.onchange('department_id')
    def onchange_department_id(self):
        result = {}
        if self.department_id:
            result['domain'] = {
                'job_id': [('department_id', '=', self.department_id.id)]}
        self.job_id = False
        return result

    @api.onchange('service_provider')
    def onchange_service_provider(self):
        result = {}
        if self.service_provider:
            result['domain'] = {'service_category_id': [
                ('service_provider', '=', self.service_provider)]}
        self.service_category_id = False
        return result

    @api.onchange('service_category_id', 'employee_id')
    def onchange_service_category_id(self):
        domain = {}
        domain_filter = []
        if self.service_category_id:
            domain_filter.append(('service_category_id',
                                  '=', self.service_category_id.id))
        if self.employee_id:
            employee = self.employee_id
            if employee.country_id.code == "SA":
                domain_filter.append(('nationality', 'in', ['saudi', False]))
            if employee.country_id.code != "SA":
                domain_filter.append(('nationality', 'in',
                                      ['non_saudi', False]))
            if employee.gender:
                domain_filter.append(('gender', 'in',
                                      [str(employee.gender), False]))
            if employee.employee_role:
                domain_filter.append(('employee_role', 'in',
                                      [str(employee.employee_role), False]))
            user_groups = self.env['res.users'].\
                browse(SUPERUSER_ID).groups_id.ids
            domain_filter.append(('group_id', 'in', user_groups))
            domain.update({'service_type_id': domain_filter})
        return {'domain': domain}

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
        onchnage employee id
        :return:
        """
        result = {'value': {'department_id': False}}
        if self.employee_id:
            if self.employee_id.department_id:
                result['value'].update({
                    'department_id': self.employee_id.department_id.id
                })
            if self.employee_id.company_id:
                result['value'].update({
                    'company_id': self.employee_id.company_id.id
                })
            if self.employee_id.f_employee_no:
                result['value'].update({
                    'f_employee_no': self.employee_id.f_employee_no
                })
            result['value'].update({
                'employee_id_view': self.employee_id.id
            })
        return result

    @api.multi
    def unlink(self):
        for service in self:
            if service.state != 'draft':
                raise ValidationError(_('You can only delete '
                                        'the draft requests!'))
        return super(service_request, self).unlink()

    @api.onchange('service_type_id')
    def onchange_service_type_id(self):
        if self.service_type_id:
            self.about_service = self.service_type_id.about_service
            self.ar_destination_required = \
                self.service_type_id.ar_destination_required
            self.en_destination_required = \
                self.service_type_id.en_destination_required
            self.quantity_required = self.service_type_id.quantity_required
            self.priority_required = self.service_type_id.priority_required
            self.completion_date_required = \
                self.service_type_id.completion_date_required
            self.details_required = self.service_type_id.details_required
            self.job_position_required = \
                self.service_type_id.job_position_required
            self.endorsement_required = \
                self.service_type_id.endorsement_required
            self.date_from_required = self.service_type_id.date_from_required
            self.date_to_required = self.service_type_id.date_to_required
            self.departure_from_required = \
                self.service_type_id.departure_from_required
            self.destination_required = \
                self.service_type_id.destination_required
            self.flight_option_required = \
                self.service_type_id.flight_option_required
            self.ar_destination = False
            self.en_destination = False
            self.quantity = False
            self.priority = False
            self.completion_date = False
            self.job_id = False
            self.date_from = False
            self.date_to = False
            if self.service_type_id.states_to_display_ids:
                self.stage_id = self.service_type_id.states_to_display_ids[
                    0].id

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.service_type_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.service_type_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.service_type_id.administration_approval:
                req_approvals.append('administration_approval')
            if service.service_type_id.oe_approval:
                req_approvals.append('oe_approval')
            if service.service_type_id.ta_approval:
                req_approvals.append('ta_approval')
            if service.service_type_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.service_type_id.finance_approval:
                req_approvals.append('finance_approval')
            if service.service_type_id.procurement_approval:
                req_approvals.append('procurement_approval')
            if service.service_type_id.ss_vp_approval:
                req_approvals.append('ss_vp_approval')
            if service.service_type_id.ceo_approval:
                req_approvals.append('ceo_approval')
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

    # All Button Comman method
    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have to check and run this code
        :return:
        """
        if self.is_transition_allowed('administration_approval'):
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

    # New [Submit for Approval]
    @api.multi
    def action_submit_for_approval(self):
        """
        method call from Button Submit for Approval
        :return:
        """
        # check condition
        if self.is_transition_allowed('mngr_approval'):
            self.service_submit_mngr()
        else:
            self._check_point_for_all_stage()

    # Button [Manager Approval]
    @api.multi
    def action_mngr_validate(self):
        """
        method call from Button Manager Approval
        :return:
        """
        # check condition
        if self.is_transition_allowed('vp_approval'):
            self.service_submit_vp()
            return True
        check_point = self._check_point_for_all_stage()
        if not check_point:
            self.service_approved()

    # Button [VP Approval]
    def action_vp_validate(self):
        """
        method call from Button VP Approval
        :return:
        """
        check_point = self._check_point_for_all_stage()
        if not check_point:
            self.service_approved()

    # Button [Admins Approval]
    @api.multi
    def validate_administration_validate(self):
        """
        Button Admins Approval
        :return:
        """
        # Check condition
        if self.is_transition_allowed('oe_approval'):
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
            self.service_approved()

    # Button OE Approval
    @api.multi
    def action_oe_validate(self):
        """
        Action OE Approval Button
        :return:
        """
        if self.is_transition_allowed('ta_approval'):
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
            self.service_approved()

    # Button TA Approval
    @api.multi
    def action_ta_validate(self):
        """
        method call from Button TA Approval
        :return:
        """
        if self.is_transition_allowed('hr_approval'):
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
            self.service_approved()

    # Button HR Approval
    @api.multi
    def action_hr_validate(self):
        """
        method call from Button HR Approval
        :return:
        """
        if self.is_transition_allowed('finance_approval'):
            self.service_validate5()
        elif self.is_transition_allowed('procurement_approval'):
            self.service_validate6()
        elif self.is_transition_allowed('ss_vp_approval'):
            self.service_validate7()
        elif self.is_transition_allowed('ceo_approval'):
            self.service_validate8()
        else:
            self.service_approved()

    # Button [Finance Approval]
    @api.multi
    def action_finance_validate(self):
        """
        method call from Button Finance Approval
        :return:
        """
        if self.is_transition_allowed('procurement_approval'):
            self.service_validate6()
        elif self.is_transition_allowed('ss_vp_approval'):
            self.service_validate7()
        elif self.is_transition_allowed('ceo_approval'):
            self.service_validate8()
        else:
            self.service_approved()

    # Button [Procurement Approval]
    @api.multi
    def action_procurement_validate(self):
        """
        method call from Button Procurement Approval
        :return:
        """
        if self.is_transition_allowed('ss_vp_approval'):
            self.service_validate7()
        elif self.is_transition_allowed('ceo_approval'):
            self.service_validate8()
        else:
            self.service_approved()

    # Button [CEO Approval]
    @api.multi
    def action_ceo_validate(self):
        """
        method call from Button CEO Approval
        :return:
        """
        self.service_approved()

    # Button [Shared Services VP Approval]
    @api.multi
    def action_ss_vp_validate(self):
        """
        method call from Button Shared Services VP Approval
        :return:
        """
        if self.is_transition_allowed('ceo_approval'):
            self.service_validate8()
        else:
            self.service_approved()

    @api.multi
    def _check_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            if not service.employee_id.gender:
                raise Warning(_("Please, You should agree on the endorsement "
                                "to proceed with your request. like Gender!"))
            attachment_mandatory = False
            if service.employee_id.gender == 'male':
                attachment_mandatory = \
                    service.service_type_id.attachment_mandatory_male
            else:
                attachment_mandatory = \
                    service.service_type_id.attachment_mandatory_female
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise Warning(_('You cannot submit the request without '
                                    'attaching a document.\n For attaching a '
                                    'document: press save then attach a '
                                    'document.'))
            if not service.employee_id.parent_id:
                raise Warning(_(
                    'Please, Ask your HR team to complete your profile data.'))
            if service.service_type_id.endorsement_required and not \
                    service.endorsement_approved:
                raise Warning(
                    _("Please, You should agree on the endorsement to proceed "
                      "with your request."))
            quantity_required = service.service_type_id.quantity_required
            request_max_quantity = service.service_type_id.request_max_quantity
            if quantity_required and service.quantity > request_max_quantity:
                raise Warning(
                    _("Please, You aren't allowed to request more than %s %s/s"
                      " per request.") %
                    (request_max_quantity, service.service_type_id.name))
            job_position_required = \
                service.service_type_id.job_position_required
            users_obj = self.env['res.users']
            if job_position_required and not users_obj.has_group(
                    'service_management.group_service_hiring_srvs'):
                raise Warning(
                    _("Please, Make sure that you have the rights to apply for"
                      "the hiring request."))
        return True

    @api.multi
    def _check_user_permissions(self, signal='approve'):
        for rec in self:
            if not rec._check_group(
                    'service_management.group_service_self_approval_srvs',
            ):
                if rec.state == 'mngr_approval' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(
                        _("Please, Make sure that you have the rights to %s "
                          "your own request.") %
                        (signal))
        return False

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = window_action_ref = False
        if service_provider == 'administration' or dest_state == \
                'administration_approval':
            if dest_state in ['administration_approval', 'finance_approval',
                              'procurement_approval', 'ss_vp_approval']:
                window_action_ref = \
                    'service_management.action_request_administration_services'
            elif dest_state in ['approved', 'refused', 'draft']:
                window_action_ref = \
                    'service_management.action_admns_service_ess_requests'
        elif service_provider == 'recruitment' or dest_state in \
                ['oe_approval', 'ta_approval']:
            if dest_state in ['oe_approval', 'ta_approval', 'finance_approval',
                              'procurement_approval', 'ss_vp_approval']:
                window_action_ref = \
                    'service_management.action_request_rcrtmnt_services'
            elif dest_state in ['approved', 'refused', 'draft']:
                window_action_ref = \
                    'service_management.action_rcrtmnt_service_ess_requests'
        elif service_provider == 'hr' or dest_state == 'hr_approval':
            if dest_state in ['hr_approval', 'finance_approval',
                              'procurement_approval', 'ss_vp_approval']:
                window_action_ref = \
                    'service_management.action_request_hr_services'
            elif dest_state in ['approved', 'refused', 'draft']:
                window_action_ref = \
                    'service_management.action_service_ess_requests'
        if dest_state in ['mngr_approval', 'vp_approval', 'ceo_approval']:
            window_action_ref = \
                'service_management.service_mngr_request_approval'
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
            'model': 'service.request'
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
    def _get_approval_delay(self, rec, req_approvals):
        diff = last_approval_date = current_state_index = False
        current_state_index = req_approvals.index(rec.state)
        if current_state_index == 0:
            last_approval_date = rec.submit_date
        else:
            previous_state = req_approvals[current_state_index - 1]
            if previous_state == 'mngr_approval':
                last_approval_date = rec.mngr_approval_date
            elif previous_state == 'vp_approval':
                last_approval_date = rec.vp_approval_date
            elif previous_state == 'administration_approval':
                last_approval_date = rec.adminis_approval_date
            elif previous_state == 'oe_approval':
                last_approval_date = rec.oe_approval_date
            elif previous_state == 'ta_approval':
                last_approval_date = rec.ta_approval_date
            elif previous_state == 'hr_approval':
                last_approval_date = rec.hr_approval_date
            elif previous_state == 'finance_approval':
                last_approval_date = rec.finance_approval_date
            elif previous_state == 'procurement_approval':
                last_approval_date = rec.procurement_approval_date
            elif previous_state == 'ss_vp_approval':
                last_approval_date = rec.ss_vp_approval_date
            elif previous_state == 'ceo_approval':
                last_approval_date = rec.ceo_approval_date
        if last_approval_date:
            last_approval_date = datetime.strptime(last_approval_date,
                                                   OE_DTFORMAT)
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            diff = relativedelta(now, last_approval_date)
        return diff

    @api.multi
    def _get_dest_email_to(self, rec):
        email_to = None
        current_state = rec.state
        if current_state == 'mngr_approval':
            email_to = rec.employee_id.service_manager_id.work_email
        elif current_state == 'vp_approval':
            email_to = rec.employee_id.service_vp_id.work_email
        elif current_state == 'administration_approval':
            email_to = rec.company_id.admins_group_email
        elif current_state == 'oe_approval':
            email_to = rec.company_id.oe_group_email
        elif current_state == 'ta_approval':
            email_to = rec.company_id.ta_group_email
        elif current_state == 'hr_approval':
            email_to = rec.company_id.hr_group_email
        elif current_state == 'finance_approval':
            email_to = rec.company_id.fi_group_email
        elif current_state == 'procurement_approval':
            email_to = rec.company_id.prcrmnt_group_email
        elif current_state == 'ss_vp_approval':
            email_to = rec.company_id.ss_vp_email
        elif current_state == 'ceo_approval':
            email_to = rec.employee_id.service_ceo_id.work_email
        return email_to

    @api.multi
    def send_reminder(self):
        # context = dict(context or {})
        delay_to_remind = 1
        # If there is no any linked reminder criteria,
        # the system will send a daily reminder.
        where_clause = [
            ('state', 'not in', ['draft', 'refused', 'approved']),
            ('submit_date', '<', datetime.now().strftime('%Y-%m-%d 00:00:00'))
        ]
        excluded_ids = self.search(where_clause)
        for rec in excluded_ids:
            req_approvals = rec._get_service_req_approvals()
            if rec.state in req_approvals:
                # It may happen in case of changing the required approvals
                # before finalizing the pending, so it will be skipped.
                approval_delay_diff = rec._get_approval_delay(rec,
                                                              req_approvals)
                if rec.service_type_id.approval_reminder_line:
                    delay_to_remind = \
                        rec.service_type_id.approval_reminder_line.delay
                if approval_delay_diff.days > delay_to_remind:
                    email_to = self._get_dest_email_to(rec)
                    rec._send_email(
                        'service_management.'
                        'approval_reminder_cron_email_template',
                        email_to,
                        rec.state,
                        rec.service_provider,
                    )
        return True

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
        service_states.append('approved')  # to add the approved state
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    @api.multi
    def _get_related_stage_id(self, service, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state))])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    def _get_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_related_stage_id(service, dest_state)
        if not stage_id:
            raise Warning(_(
                "Stage ID not found, Please Configure Service Stages for "
                "%s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'submitted_by': self.env.user.id,
                           'submit_date': self._get_current_datetime()})
        if current_state == 'mngr_approval':
            result.update(
                {'state': dest_state, 'mngr_user_id': self.env.user.id,
                 'mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp_approval':
            result.update({'state': dest_state, 'vp_user_id': self.env.user.id,
                           'vp_approval_date': self._get_current_datetime()})
        if current_state == 'administration_approval':
            result.update(
                {'state': dest_state, 'adminis_user_id': self.env.user.id,
                 'adminis_approval_date': self._get_current_datetime()})
        if current_state == 'oe_approval':
            result.update({'state': dest_state, 'oe_user_id': self.env.user.id,
                           'oe_approval_date': self._get_current_datetime()})
        if current_state == 'ta_approval':
            result.update({'state': dest_state, 'ta_user_id': self.env.user.id,
                           'ta_approval_date': self._get_current_datetime()})
        if current_state == 'hr_approval':
            result.update({'state': dest_state, 'hr_user_id': self.env.user.id,
                           'hr_approval_date': self._get_current_datetime()})
        if current_state == 'finance_approval':
            result.update(
                {'state': dest_state, 'finance_user_id': self.env.user.id,
                 'finance_approval_date': self._get_current_datetime()})
        if current_state == 'procurement_approval':
            result.update(
                {'state': dest_state, 'procurement_user_id': self.env.user.id,
                 'procurement_approval_date': self._get_current_datetime()})
        if current_state == 'ss_vp_approval':
            result.update(
                {'state': dest_state, 'ss_vp_user_id': self.env.user.id,
                 'ss_vp_approval_date': self._get_current_datetime()})
        if current_state == 'ceo_approval':
            result.update(
                {'state': dest_state, 'ceo_user_id': self.env.user.id,
                 'ceo_approval_date': self._get_current_datetime()})
        return result

    @api.multi
    def service_submit_mngr(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email('service_management.service_mngr_email_tmplt',
                                 None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_submit_vp(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_vp_email_tmplt',
                    None, dest_state, service.service_provider,
                )
                return True

    @api.multi
    def service_validate1(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_admins_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_validate2(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(self._get_approval_info(service, dest_state))
                # Email Tamplet not find
                # self._send_email('service_management.service_oe_srvr_action',
                #                  None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_validate3(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_ta_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_validate4(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_hr_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_validate5(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_fi_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_validate6(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_prcrmnt_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_validate7(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_ss_vp_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_validate8(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self._send_email(
                    'service_management.service_ceo_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_approved(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                result = self._get_approval_info(service, dest_state)
                final_approval = {
                    'final_approval_user_id': self.env.user.id,
                    'final_approval_date': self._get_current_datetime()
                }
                result.update(final_approval)
                self.write(result)
                self._send_email(
                    'service_management.service_aprvd_email_tmplt',
                    None, dest_state, service.service_provider)
                return True

    @api.multi
    def service_refused(self):
        '''
        Open the wizard for Refuse Reason
        :return:Wizard
        '''
        for rec in self:
            self._check_user_permissions('refuse')
            stage_id = self._get_related_stage_id(rec,
                                                  'refused')
            view = self.env.ref('service_management.refuse_service_form_view')
            if stage_id:
                return {
                    'name': _('Refuse Reason'),
                    'context': self._context,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'refuseservice.reason',
                    'views': [(view.id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }

    @api.multi
    def action_refused(self):
        for service in self:
            self._check_user_permissions('refuse')
            stage_id = self._get_related_stage_id(service,
                                                  'refused')
            if stage_id:
                self.write({'stage_id': stage_id.id,
                            'state': 'refused',
                            'refused_by': self.env.user.id,
                            'refuse_date': self._get_current_datetime(),
                            })
            self._send_email(
                'service_management.service_rfus_email_tmplt',
                'refused', None, service.service_provider)
            return True

    @api.multi
    def reset_to_draft(self):
        for service in self:
            stage_id = self._get_related_stage_id(service,
                                                  'draft')
            self.write({
                'state': 'draft',
                'stage_id': stage_id.id,
                'submit_date': False,
                'submitted_by': False,
                'final_approval_user_id': False,
                'final_approval_date': False,
                'mngr_user_id': False,
                'mngr_approval_date': False,
                'vp_user_id': False,
                'vp_approval_date': False,
                'adminis_user_id': False,
                'adminis_approval_date': False,
                'oe_user_id': False,
                'oe_approval_date': False,
                'ta_user_id': False,
                'ta_approval_date': False,
                'hr_user_id': False,
                'hr_approval_date': False,
                'finance_user_id': False,
                'finance_approval_date': False,
                'procurement_user_id': False,
                'procurement_approval_date': False,
                'ss_vp_user_id': False,
                'ss_vp_approval_date': False,
                'ceo_user_id': False,
                'ceo_approval_date': False,
                'refused_by': False,
                'refuse_date': False,
                'returned_by': self.env.user.id,
                'return_date': self._get_current_datetime(),
                'waiting_time': False,
                'expected_approval_date_as_sla': False,
            })
            # wf_service = netsvc.LocalService("workflow")
            # for id in ids:
            self._send_email(
                'service_management.service_rtrnd_email_tmplt',
                None, 'draft', service.service_provider)
            # this workflow need to be migrate
            # wf_service.trg_create(uid, 'service.request', id, cr)
            return True

    # @api.multi
    # def action_submit(self):
    #     ir_obj = self.env['ir.attachment']
    #
    #     for service in self:
    #         attachment_mandatory = service.service_type_id. \
    #             attachment_mandatory
    #         if attachment_mandatory:
    #             existing_attachement = ir_obj.search([
    #                 ('res_id', '=', service.id)])
    #             if not existing_attachement:
    #                 raise ValidationError(_(
    #                     'You cannot submit the request '
    #                     'without attaching a document.'
    #                     '\n For attaching a document: '
    #                     'press save then attach a document.'))
    #
    #         dest_state = self._get_dest_state(service)
    #         if dest_state:
    #             return self.write({'state': dest_state})
    #         else:
    #             raise ValidationError(_('Service Bad '
    #                                     'Configuration!'))

    @api.multi
    def action_approve(self):
        for service in self:
            dest_state = self._get_dest_state(service)
            if dest_state:
                return self.write(self._get_approval_info(service, dest_state))

    @api.multi
    def action_refuse(self):
        return self.write({'state': 'refused', 'refused_by': self.env.uid,
                           'refuse_date': self._get_current_datetime()})

    # @api.multi
    # def action_reset_to_draft(self):
    #     return self.write({'state': 'draft'})

    # @api.multi
    # def action_mark_as_done(self):
    #     return self.write({'state': 'done'})

    # @api.multi
    # def action_top_mngmnt_validate(self):
    #     for service in self:
    #         dest_state = self._get_dest_state(service)
    #         if dest_state:
    #             return self.
    # write(self._get_approval_info(service, dest_state))

    # @api.multi
    # def action_hr_validate(self):
    #     for service in self:
    #         dest_state = self._get_dest_state(service)
    #         if dest_state:
    #             return self.
    # write(self._get_approval_info(service, dest_state))

    # @api.multi
    # def action_infrastructure_validate(self):
    #     for service in self:
    #         dest_state = self._get_dest_state(service)
    #         if dest_state:
    #             return self.write({
    #                 'state': dest_state,
    #                 'fourth_user_id': self.env.uid,
    #                 'fourth_approval_date': self._get_current_datetime()
    #             })
    #
    # @api.multi
    # def action_administration_validate(self):
    #     for service in self:
    #         dest_state = self._get_dest_state(service)
    #         if dest_state:
    #             return self.write({
    #                 'state': dest_state,
    #                 'fourth_user_id': self.env.uid,
    #                 'fourth_approval_date': self._get_current_datetime()
    #             })

    @api.multi
    def action_cancel(self):
        return self.write({
            'state': 'cancelled'
        })
