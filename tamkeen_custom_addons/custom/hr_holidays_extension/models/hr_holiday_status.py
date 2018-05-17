from pytz import common_timezones
from odoo import models, api, fields, _


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'
    _order = 'display_sequence'

    @api.model
    def _tz_list(self):
        res = tuple()
        for name in common_timezones:
            res += ((name, name),)
        return res

    @api.multi
    def name_get(self):
        result = []
        for status in self:
            result.append((status.id, status.name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('group_filter'):
            user_groups = self.env.user.groups_id.ids
            filter_rec = []
            for rec in self.search([]):
                if rec.authorized_group:
                    if rec.authorized_group.id in user_groups:
                        filter_rec.append(rec.id)
            return self.browse(filter_rec).name_get()
        return super(HrHolidaysStatus, self).name_search(name, args=None,
                                                         operator='ilike',
                                                         limit=100)

    is_gender = fields.Boolean(string='Gender')
    is_religion = fields.Boolean(string='Religion')
    authorized_group = fields.Many2one('res.groups', 'Authorized Group')
    gender = fields. \
        Selection([('m', 'Male'),
                   ('f', 'Female')],
                  string='Gender',
                  index=True)
    religion = fields. \
        Selection([('m', 'Muslim'),
                   ('o', 'Other')],
                  string='Religion', index=True)
    ex_rest_days = fields. \
        Boolean(string='Exclude Rest Days',
                help="If enabled, the employee's "
                     "day off is skipped in leave"
                     " days calculation.")
    ex_public_holidays = fields. \
        Boolean(string='Exclude Public Holidays',
                help="If enabled, public holidays"
                     " are skipped in leave days calculation.")
    enable_min_day = fields. \
        Boolean(string='Enable Min Days',
                help="If enabled, the system"
                     " will not count the"
                     " restdays if the"
                     " employee attendaded"
                     " in a week the min day")
    min_days = fields. \
        Integer(string='Minimum Days',
                digits=(16, 1),
                help="Minimum number of"
                     " days the employee should"
                     " at least attend so it"
                     " won't count the rest days.")
    max_days = fields. \
        Integer(string='Maximum Allowed Days Per Request', digits=(16, 1),
                help="Maximum number of days the"
                     " employee should take ,so it"
                     " won't count the rest days.")
    # attachment_mandatory_male = fields.Boolean(
    #     string='Attachment is mandatory for Male')
    # attachment_mandatory_female = fields.Boolean(
    #     string='Attachment is mandatory for Female')
    alternative_emp_mandatory = fields. \
        Boolean(string='Alternative employee is mandatory')
    ceo_number = fields.Integer(string='CEO day limit')
    manager_appr = fields. \
        Boolean(string='Manager Approval')
    hr_appr = fields. \
        Boolean(string='HR Approval')
    ceo_appr = fields. \
        Boolean(string='CEO Approval')
    vp_appr = fields. \
        Boolean(string='VP Approval')
    allow_trial_period = fields.Boolean(
        string='Trial Period Exception',
        help='Allow the employees to apply'
             ' for this leave type even'
             ' if he/she in the trial period.')
    allow_future_balance = fields.Boolean(
        "Allow Future Balance",
        help="Allow the calculation of future leave for this type.")
    # hr_seniour = fields.Boolean(string='HR Seniour Approval')
    # notif_mngr_approval = fields.Boolean('Manager Approval')
    # notif_ceo_approval = fields.Boolean('CEO Approval')
    # hr_notify_approval = fields.Boolean('HR Approval')
    # vp_notify_approval = fields.Boolean("VP Approval")
    notif_leave_refuse = fields.Boolean('Leave Refuse')
    notif_leave_amend = fields.Boolean('Leave Amend')
    notif_leave_cancel = fields.Boolean('Leave Cancel')
    work_resum_to_manager = fields.Boolean('Leave Cancel')
    work_resum_by_manager = fields.Boolean()
    work_resum_by_hr_manager = fields.Boolean()
    check_locked_balance = fields.Boolean('Check Locked Balance')
    preliminary_leave = fields.Many2one('hr.holidays.status',
                                        'Preliminary Leave')
    can_exceed_maximum_allowed_days = fields.Boolean(string='Can Exceed '
                                                            'Maximum '
                                                            'Allowed Days',
                                                     default=True)
    # require_allocation = fields.Boolean(string='Require Allocation')
    leaves_calculation_calendar = fields.Selection([('normal', 'Normal'),
                                                    ('hijri', 'Hijri'),
                                                    ('sick', 'Sick')],
                                                   string='Leaves '
                                                          'Calculation '
                                                          'Calendar')
    maximum_accumulative_balance_per_calendar = fields.Float(string='Maximum Accumulative Balance Per Calendar')
    maximum_allowed_days_per_payroll_period = fields.Float(string='Maximum Allowed Days Per Payroll Period')
    maximum_allowed_days_per_year = fields.Float(
        string='Maximum Allowed Days Per Year')
    approval_reminder_line = fields.Many2one('approval.reminder.line.panel',
                                             'Reminder Criteria')
    display_sequence = fields.Integer('Display Sequence')
    tz = fields.Selection(_tz_list, string='Time Zone')
    submit_message = fields.Text('Submit Hint Message')
    reply_email = fields.Char(string='Reply Email', help='This field will '
                                                         'be used in case of '
                                                         'any reply on any '
                                                         'email from this '
                                                         'service.')
    proof_required = fields.Boolean(string='Proofs Required')
    leave_type_proof_ids = fields.Many2many('leave.type.proof.documents',
                                         'leave_type_proof_document_rel',
                                         'proof_id', 'leave_type_id',
                                         string='Leave Proofs')
    about_leave_type = fields.Text('About Leave Type')
    carry_forward_balance = fields.Float(string='Carry Forward Balance')
    hr_email = fields.Char(string='HR Email')
    vp_approval = fields.Boolean(string='VP Approval')
    ignore_locked_period = fields.Boolean(string='Ignore Locked Period',
                                          help='Allow the employees to apply '
                                               'for this leave type even if '
                                               'the leave period within a '
                                               'locked payroll period.')
    code = fields.Char(string='Code')
    arabic_name = fields.Char(string='Arabic Name')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)',
         'Codes for leave types must be unique!')]

    @api.multi
    def get_days(self, employee_id):
        # need to use `dict` constructor to create a dict per id
        result = dict((id,
                       dict(max_leaves=0, leaves_taken=0, remaining_leaves=0,
                            virtual_remaining_leaves=0)) for id in self.ids)

        holidays = self.env['hr.holidays'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'vp', 'validate1', 'ceo', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        for holiday in holidays:
            status_dict = result[holiday.holiday_status_id.id]
            if holiday.type == 'add' and holiday.active:
                if holiday.state == 'validate':
                    # note: add only validated allocation even for the virtual
                    # count; otherwise pending then refused allocation allow
                    # the employee to create more leaves than possible
                    status_dict[
                        'virtual_remaining_leaves'] += holiday.number_of_days_temp
                    status_dict['max_leaves'] += holiday.number_of_days_temp
                    status_dict[
                        'remaining_leaves'] += holiday.number_of_days_temp
            elif holiday.type == 'remove':  # number of days is negative
                status_dict[
                    'virtual_remaining_leaves'] -= holiday.number_of_days_temp
                if holiday.state == 'validate':
                    status_dict['leaves_taken'] += holiday.number_of_days_temp
                    status_dict[
                        'remaining_leaves'] -= holiday.number_of_days_temp
        return result


class LeaveTypeProofDocuments(models.Model):
    _name = 'leave.type.proof.documents'

    name = fields.Char(string='Name')
    mandatory = fields.Boolean('Mandatory')
    description = fields.Text('Description')
    document = fields.Binary('Document')
    document_file_name = fields.Char('File Name')