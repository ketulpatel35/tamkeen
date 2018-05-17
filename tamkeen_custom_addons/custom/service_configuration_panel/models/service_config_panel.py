from odoo import models, api, fields, _
from odoo.addons.hr_employee_marked_roles.models.hr import ROLE
from pytz import common_timezones
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DTFORMAT

SERVICE_STATUS = [('draft', 'To Submit'),
                  ('mngr_approval', 'Manager Approval'),
                  ('vp_approval', 'VP Approval'),
                  # ('administration_approval', 'Administration Approval'),
                  ('hr_approval', 'HR Approval'),
                  # ('finance_approval', 'Finance Approval'),
                  ('budget_approval', 'Budget Approval'),
                  # ('procurement_approval', 'Procurement Approval'),
                  ('final_hr_approval', 'HR Review'),
                  ('ceo_approval', 'CEO Approval'),
                  ('approved', 'Approved'),
                  ('rejected', 'Rejected'),
                  ('open', 'Open'),
                  ('locked', 'Locked'),
                  ('closed', 'Closed'),
                  ('cancelled', 'Cancelled'),
                  ('done', 'Done'),
                  ('payroll_processing',
                   'Payroll Processing'),
                  ('finance_processing', 'Finance Processing'),
                  ('waiting_repayment', 'Waiting Re-Payment')]
SLA_UNIT = [('minutes', 'Minute/s'), ('hours', 'Hour/s'), ('days', 'Day/s')]


class ApprovalReminderLinePanel(models.Model):
    _name = 'approval.reminder.line.panel'
    _description = 'Approval Reminder Criteria Panel'

    name = fields.Char(string='Name', required=True)
    delay = fields.Integer(
        string='Maximum Delay',
        help="The number of days "
             "to wait before sending the reminder.",
        required=True)


class service_panel_displayed_states(models.Model):
    _name = 'service.panel.displayed.states'
    _order = 'sequence'

    # @api.model
    # def get_wkf_state(self):
    # SERVICE_STATUS = [('draft', 'To Submit'),
    #                   ('mngr_approval', 'Manager Approval'),
    #                   ('vp_approval', 'VP Approval'),
    #                   ('administration_approval',
    #                    'Administration Approval'),
    #                   ('hr_approval', 'HR Approval'),
    #                   ('finance_approval', 'Finance Approval'),
    #                   ('budget_approval', 'Budget Approval'),
    #                   ('procurement_approval', 'Procurement Approval'),
    #                   ('ceo_approval', 'CEO Approval'),
    #                   ('approved', 'Approved'),
    #                   ('refused', 'Refused')]
    # return SERVICE_STATUS

    name = fields.Char(string='State Name', required=True, translate=True)
    sequence = fields.Integer('Sequence')
    wkf_state = fields.Selection(SERVICE_STATUS, 'Related State',
                                 required=True)
    case_default = fields.Boolean(
        string='Default for New Services',
        help="If you check this field, this stage will be proposed by default "
             "on each new service type. It will not assign this stage to "
             "existing services.")
    service_type_ids = fields.Many2many(
        'service.configuration.panel',
        'service_panel_states_rel',
        'state_id',
        'srvc_type_id',
        string="Services Types")
    model_id = fields.Many2one('ir.model', string='Add-on')
    is_model_found = fields.Boolean('Is Model Found', default=False)

    _sql_constraints = [
        ('wkf_state_unique', 'unique(wkf_state,model_id)',
         'You should select one state per a stage.')]


class service_configuration_panel(models.Model):
    _name = 'service.configuration.panel'
    _order = 'display_sequence asc, name'
    _inherit = ['mail.thread']

    # @api.model
    # def _get_group_id(self):
    #     group_id = False
    #     dataobj = self.env['ir.model.data']
    #     try:
    #         dummy, group_id = dataobj.get_object_reference(
    #             'service_management', 'group_service_user')
    #     except ValueError:
    #         pass
    #     return group_id

    # @api.model
    # def _get_type_common(self):
    #     ids = self.env['service.panel.displayed.states'].search([
    #         ('case_default', '=', 1)])
    #     return ids

    @api.model
    def _tz_list(self):
        res = tuple()
        for name in common_timezones:
            res += ((name, name),)
        return res

    name = fields.Char('Service Name', size=250,
                       required=True, translate=True)
    code = fields.Char('Service Code', size=250,
                       required=True)
    parent_id = fields.Many2one('service.configuration.panel', string='Parent')
    active = fields.Boolean('Active',
                            help="If the active field is set to false, "
                                 "it will allow you to hide the requests "
                                 "type without removing it.",
                            default=True)
    mngr_approval = fields.Boolean('Manager Approval')
    vp_approval = fields.Boolean('VP Approval')
    hr_approval = fields.Boolean('HR Approval')
    hr_email = fields.Char(string='HR Email')
    # infrastructure_approval = fields.Boolean('Infrastructure Approva######l')
    finance_approval = fields.Boolean('Finance Approval')
    finance_email = fields.Char(string='Finance Email')
    budget_approval = fields.Boolean('Budget Approval')
    budget_email = fields.Char(string='Budget Email')
    procurement_approval = fields.Boolean('Procurement Approval')
    procurement_email = fields.Char(string='Procurement Email')
    ceo_approval = fields.Boolean('CEO Approval')
    administration_approval = fields.Boolean('Administration Approval')
    administration_email = fields.Char(string='Administration Email')
    # service_provider = fields.Selection(
    #     SRVC_PRVDR,
    #     'Service Provider',
    #     required=True,
    #     help="The responsible business unit for granting this service.")
    # service_category_id = fields.Many2one('service.category',
    #                                        'Service Category', required=True)
    # general_service = fields.Boolean('General Service')
    # hr_service = fields.Boolean('HR Service')
    # infrastructure_service = fields.Boolean('Infrastructure Service')
    # administration_service = fields.Boolean('Administration Service')
    nationality = fields.Selection(
        [('saudi', 'Saudi'), ('non_saudi', 'Non Saudi')], 'Nationality',
        help="The service will be displayed for the selected nationality, "
             "empty for all")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              'Gender',
                              help="This means that this service will be "
                                   "displayed for the selected gender.")
    request_max_quantity = fields.Float('Maximum Quantity',
                                        help='Maximum quantity per request.')
    attachment_mandatory = fields.Boolean('Attachment/s Required')
    # for_non_saudi = fields.Boolean('For Non Saudi',
    #                                help="If you selected this attribute, "
    #                                     "it will be displayed for the non "
    #                                     "saudi employees only.")
    quantity_required = fields.Boolean('Quantity Required')
    priority_required = fields.Boolean('Priority Required')
    details_required = fields.Boolean('Details Required')
    about_service = fields.Text('About The Service',
                                required=True)
    sla_period = fields.Integer('SLA Period')
    sla_period_unit = fields.Selection(SLA_UNIT, 'SLA Period Unit')
    display_sequence = fields.Integer('Display Sequence')
    # group_id = fields.Many2one(
    #     'res.groups',
    #     'Authorized Group',
    #     required=True,
    #     default=_get_group_id,
    #     help="The group that a user must have to be authorized to view this "
    #          "service type.")
    employee_role = fields.Selection(ROLE, 'Related Employee Role')
    states_to_display_ids = fields.Many2many(
        'service.panel.displayed.states',
        'service_panel_states_rel',
        'srvc_type_id',
        'state_id',
        required=True,
        string="States To Be Displayed",
        help="Please, select the states based on the selected workflow "
             "approvals.")
    endorsement_required = fields.Boolean('Endorsement Required')
    endorsement_text = fields.Text('Endorsement Text')
    file_to_fill = fields.Binary('File To Fill')  # ,filters='*.xml'),
    approval_reminder_line = fields.Many2one('approval.reminder.line.panel',
                                             'Reminder Criteria')
    valid_from_date = fields.Date(string='Valid From Date')
    valid_to_date = fields.Date(string='Valid To Date')
    submit_message = fields.Text('Submit Hint Message')
    reply_email = fields.Char(string='Reply Email', help='This field will '
                                                         'be used in case of '
                                                         'any reply on any '
                                                         'email from this '
                                                         'service.')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 readonly=True,
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get())
    tz = fields.Selection(_tz_list, string='Time Zone')
    model_id = fields.Many2one('ir.model', string='Add-on')
    track_logs = fields.Boolean(string='Track Logs', default=True)
    payroll_run_day = fields.Integer(string='Payroll Run Day')
    service_proof_ids = fields.Many2many('service.proof.documents',
                                         'loan_proof_service_panel_rel',
                                         'proof_id', 'service_id',
                                         string='Service Proofs')
    proof_required = fields.Boolean(string='Proofs Required')
    journal_id = fields.Many2one('account.journal', string='Related Journal')
    product_id = fields.Many2one('product.product', string='Related Product')

    @api.multi
    @api.constrains('valid_from_date', 'valid_to_date')
    def _check_date_validations(self):
        for rec in self:
            if rec.valid_from_date and rec.valid_to_date:
                date_from = datetime.strptime(rec.valid_from_date,
                                              DTFORMAT).date()
                date_to = datetime.strptime(rec.valid_to_date,
                                            DTFORMAT).date()
                if date_to < date_from:
                    raise Warning(_('Date From must be Greter then Date to!'))

class ServiceLog(models.Model):
    _name = 'service.log'

    user_id = fields.Many2one('res.users', string='User')
    activity_datetime = fields.Datetime(string='Activity Datetime')
    state_from = fields.Char(string='State From')
    state_to = fields.Char(string='State To')
    reason = fields.Text(string='Reason')


class ServiceProofDocuments(models.Model):
    _name = 'service.proof.documents'

    model_id = fields.Many2one('ir.model', string='Add-on')
    name = fields.Char(string='Name')
    mandatory = fields.Boolean('Mandatory')
    description = fields.Text('Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def default_get(self, fields_list):
        res = super(ServiceProofDocuments, self).default_get(fields_list)
        if self._context:
            if self._context.get('model_id'):
                res.update({'model_id': self._context.get(
                    'model_id')})
        return res
