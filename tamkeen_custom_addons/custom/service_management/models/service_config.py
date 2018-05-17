# -*- encoding: utf-8 -*-
from odoo import api, fields, models
from service import SERVICE_STATUS
from odoo.addons.hr_employee_marked_roles.models.hr import ROLE

# ROLE = ROLE or [('staff', 'Staff'), ('director', 'Director'),
#                 ('vp', 'Vice President'), ('ceo', 'CEO')]

SRVC_PRVDR = [('hr', 'HR'), ('administration', 'Administration'),
              ('recruitment', 'Recruitment')]
SLA_UNIT = [('minutes', 'Minute/s'), ('hours', 'Hour/s'), ('days', 'Day/s')]


class approval_reminder_line(models.Model):
    _name = 'approval.reminder.line'
    _description = 'Approval Reminder Criteria'
    name = fields.Char(string='Name', required=True)
    delay = fields.Integer(
        string='Maximum Delay',
        help="The number of days "
             "to wait before sending the reminder.",
        required=True)


class service_displayed_states(models.Model):
    _name = 'service.displayed.states'
    _order = 'sequence'

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
        'service.type',
        'service_states_rel',
        'state_id',
        'srvc_type_id',
        string="Services Types")

    _sql_constraints = [
        ('wkf_state_unique',
         'unique(wkf_state)',
         'You should select one state per a stage.')]


class service_category(models.Model):
    _name = "service.category"
    _description = "Service Category"
    _order = 'display_sequence asc, name'
    _inherit = ['mail.thread']

    name = fields.Char('Name', size=250, required=True,
                       translate=True)
    service_provider = fields.Selection(
        SRVC_PRVDR,
        string='Service Provider',
        required=True,
        help="The responsible business unit for granting this service.")
    active = fields.Boolean(string='Active', default="True")
    code = fields.Char(string='Code')
    display_sequence = fields.Integer(string='Display Sequence')


class service_type(models.Model):
    _name = "service.type"
    _description = "Service Type"
    _inherit = ['mail.thread']
    _order = 'display_sequence asc, name'

    @api.model
    def _get_group_id(self):
        group_id = False
        dataobj = self.env['ir.model.data']
        try:
            dummy, group_id = dataobj.get_object_reference(
                'service_management', 'group_service_user')
        except ValueError:
            pass
        return group_id

    @api.model
    def _get_type_common(self):
        ids = self.env['service.displayed.states'].search([
            ('case_default', '=', 1)])
        return ids

    name = fields.Char('Service Name', size=250,
                       required=True, translate=True)
    active = fields.Boolean('Active',
                            help="If the active field is set to false, "
                                 "it will allow you to hide the requests "
                                 "type without removing it.",
                            default=True)
    mngr_approval = fields.Boolean('Manager Approval')
    vp_approval = fields.Boolean('VP Approval')
    oe_approval = fields.Boolean('Organization Effectiveness Approval')
    ta_approval = fields.Boolean('Talent Acquisition Approval')
    hr_approval = fields.Boolean('HR Approval')
    hr_email = fields.Char(string='HR Email')
    # infrastructure_approval = fields.Boolean('Infrastructure Approva######l')
    ss_vp_approval = fields.Boolean('Shared Services VP Approval')
    finance_approval = fields.Boolean('Finance Approval')
    procurement_approval = fields.Boolean('Procurement Approval')
    ceo_approval = fields.Boolean('CEO Approval')
    administration_approval = fields.Boolean('Administration Approval')
    administration_email = fields.Char(string='Administration Email')
    service_category_id = fields.Many2one('service.category',
                                          'Service Category')
    service_provider = fields.Selection(
        SRVC_PRVDR,
        'Service Provider',
        required=True,
        help="The responsible business unit for granting this service.")
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
    ar_destination_required = fields.Boolean('Destination Required (AR)')
    en_destination_required = fields.Boolean('Destination Required (EN)')
    attachment_mandatory_male = fields.Boolean('Attachment/s Required for '
                                               'Male')
    attachment_mandatory_female = fields.Boolean('Attachment/s Required for '
                                                 'Female')
    # for_non_saudi = fields.Boolean('For Non Saudi',
    #                                help="If you selected this attribute, "
    #                                     "it will be displayed for the non "
    #                                     "saudi employees only.")
    quantity_required = fields.Boolean('Quantity Required')
    priority_required = fields.Boolean('Priority Required')
    details_required = fields.Boolean('Details Required')
    completion_date_required = fields.Boolean('Expected '
                                              'Completion Date Required')
    about_service = fields.Text('About The Service',
                                required=True)
    job_position_required = fields.Boolean('Job Position Required')
    sla_period = fields.Integer('SLA Period')
    sla_period_unit = fields.Selection(SLA_UNIT, 'SLA Period Unit')
    display_sequence = fields.Integer('Display Sequence')
    group_id = fields.Many2one(
        'res.groups',
        'Authorized Group',
        required=True,
        default=_get_group_id,
        help="The group that a user must have to be authorized to view this "
             "service type.")
    employee_role = fields.Selection(ROLE, 'Related Employee Role')
    states_to_display_ids = fields.Many2many(
        'service.displayed.states',
        'service_states_rel',
        'srvc_type_id',
        'state_id',
        required=True,
        default=_get_type_common,
        string="States To Be Displayed",
        help="Please, select the states based on the selected workflow "
             "approvals.")
    endorsement_required = fields.Boolean('Endorsement Required')
    endorsement_text = fields.Text('Endorsement Text')
    file_to_fill = fields.Binary('File To Fill')  # ,filters='*.xml'),
    approval_reminder_line = fields.Many2one('approval.reminder.line',
                                             'Reminder Criteria')
    date_from_required = fields.Boolean('Date From Required')
    date_to_required = fields.Boolean('Date To Required')
    departure_from_required = fields.Boolean('Departure From Required')
    destination_required = fields.Boolean('Destination Required')
    flight_option_required = fields.Boolean('Flight Option Required')

    @api.onchange('service_provider')
    def onchange_service_provider(self):
        result = {}
        if self.service_provider:
            result['domain'] = {'service_category_id': [
                ('service_provider', '=', self.service_provider)]}
        self.service_category_id = False
        return result
