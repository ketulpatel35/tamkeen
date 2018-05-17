from odoo import models, fields, api, _, exceptions
from odoo.exceptions import Warning
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import ValidationError
from pytz import timezone


class AttendanceChangeReason(models.Model):
    _name = 'attendance.change.reason'
    _description = 'Employee Attendance Change Reason'

    name = fields.Char(sring='Name')
    code = fields.Char(sring='Code')
    onsite = fields.Boolean(string='Onsite')
    permission = fields.Boolean(sring='Permission')
    sign_in = fields.Boolean(sring='Sign In')
    sign_out = fields.Boolean(sring='Sign Out')


class AttendanceConfiguration(models.Model):
    _name = 'attendance.configuration'
    _description = 'Employee Attendance Configuration'

    per_day_change_request = fields.Float(string='Change Request Per Day')
    month_change_request = fields.Float(string='Change Request Per Month')
    work_from = fields.Char(string='Standard Work From')
    buffer_hours = fields.Char(string='Buffer Hours')
    work_to = fields.Char(string='Standard Work To')


class AttendanceCapture(models.Model):
    _name = 'attendance.change.request'
    _description = 'Employee Attendance Change Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'ref'

    parent_id = fields.Many2one(
        'attendance.change.request',
        string='Change Request')
    child_ids = fields.One2many('attendance.change.request', 'parent_id',
                                string='Change Request')
    employee_id = fields.Many2one('hr.employee',
                                  string="Employee",
                                  default=lambda self:
                                  self.env['hr.employee'].search([
                                      ('user_id', '=', self._uid)], limit=1) or
                                  False, track_visibility='always')
    immediate_manager = fields.Many2one('hr.employee', string="Immediate "
                                                              "Employee",
                                        related='employee_id.parent_id')
    date_from = fields.Datetime(string='Date From', default=datetime.today(),
                                track_visibility='always')
    date_to = fields.Datetime(string='Date To', default=datetime.today(),
                              track_visibility='always')
    date = fields.Date(string='Date', default=fields.Date.context_today,
                       track_visibility='always')
    change_reason_id = fields.Many2one(
        'attendance.change.reason', string='Reason', track_visibility='always')
    onsite = fields.Boolean(string='Onsite', related='change_reason_id.onsite')
    active = fields.Boolean('Active')
    permission = fields.Boolean(
        string='Permission',
        related='change_reason_id.permission')
    sign_in = fields.Boolean(
        sring='Sign In',
        related='change_reason_id.sign_in')
    sign_out = fields.Boolean(
        sring='Sign Out',
        related='change_reason_id.sign_out')
    f_employee_no = \
        fields.Char(related='employee_id.f_employee_no', string='Employee ID')
    state = fields.Selection((
        ('draft', 'Draft'),
        ('for_review', 'Manager Approval'),
        ('hr_review', 'Hr Approval'),
        ('waiting_for_attendance', 'Waiting for attendance'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ), string='State', default='draft', track_visibility='always')
    reason = fields.Text('Remarks', track_visibility='always')
    attendance_id = fields.Many2one('hr.attendance', 'Attendance')
    ref = fields.Char(string='Name')
    departement_id = fields.Many2one('hr.department', string='Department',
                                     related='employee_id.department_id')
    active = fields.Boolean(string='Active', default=True)

    @api.constrains('date_from', 'date_to')
    def _check_change_request_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for change_request in self:
            if change_request.date_from and change_request.date_to:
                if change_request.date_from > change_request.date_to:
                    raise exceptions.ValidationError(_(
                        '"Date To" time cannot be earlier than "Date From" '
                        'time.'))

    @api.multi
    def compute_attendance_id(self):
        """
        :return:
        """
        for rec in self:
            rec.attendance_count = len(rec.attendance_id)

    attendance_count = fields.Integer(compute='compute_attendance_id')

    # diff_date_total = fields.Integer(string='Diff Date Total',
    #                                  compute='_get_date_diff')

    @api.multi
    def action_view_attendance(self):

        return {
            'type': 'ir.actions.act_window',
            'name': _('Attendance Change Request'),
            'res_model': 'hr.attendance',
            'view_mode': 'form',
            'view_type': 'form',
            'domain': [('id', 'in', self.attendance_id.id)],
            'res_id': self.attendance_id.id,
            'target': 'current',
        }

    def get_default_change_reason(self):
        change_reason_rec = self.env['attendance.change.reason'].search([(
            'permission', '=',
            True)], limit=1)
        return change_reason_rec

    @api.model
    def default_get(self, fields):
        res = super(AttendanceCapture, self).default_get(fields)
        change_reason_rec = self.get_default_change_reason()
        if change_reason_rec:
            res.update({'change_reason_id': change_reason_rec.id})
        return res

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('seq.change.request')
        vals.update({'ref': name})
        return super(AttendanceCapture, self).create(vals)

    def riyadh_timezone(self, date):
        gmt_tz = timezone('GMT')
        if self.env.user and self.env.user.tz:
            local_tz = timezone(self.env.user.tz)
        else:
            local_tz = timezone('Asia/Riyadh')
        if date:
            gmt_utcdt = (gmt_tz.localize(date))
            riyadh_dt = gmt_utcdt.astimezone(local_tz)
            return riyadh_dt
        return date

    @api.multi
    def _check_group(self, group_xml_id):
        users_obj = self.env['res.users']
        if users_obj.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def _check_user_permissions(self, signal='approve'):
        if not self._check_group('hr_attendance_customization.'
                                 'group_attendance_self_approval_srvs'):
            for rec in self:
                if rec.state == 'for_review' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(
                        _("Please, Make sure that you have the rights to %s "
                          "your own request.") %
                        (signal))
        return False

    @api.multi
    def _set_email_template_context(self, data_pool, template_pool,
                                    email_to, dest_state, service_provider):
        ir_model_data = self.env['ir.model.data']
        context = dict(self._context)
        display_link = False
        base_url = self.env['ir.config_parameter']. \
            get_param('web.base.url.static')
        action_id = False
        window_action_id = window_action_ref = False
        window_action_ref = \
            'attendance_change_request.attendance_change_request_action'

        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            action_id = ir_model_data.get_object_reference(
                addon_name, window_action_id)[1] or False

        if action_id:
            display_link = True
        context.update({
            'base_url': base_url,
            'display_link': display_link,
            'action_id': action_id,
            'model': 'attendance.change.request',
        })
        return context

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
    def request_cancel(self):
        """
        request rejected
        :return:
        """
        for rec in self:
            rec._check_user_permissions('approve')
            rec.state = 'cancel'
            rec._send_email(
                'attendance_change_request.'
                'email_template_change_request_cancelation',
                None, 'cancel', rec.id, 'attendance_change_request')

    @api.multi
    def set_state_to_draft(self):
        """
        set to draft
        :return:
        """
        for rec in self:
            rec._check_user_permissions('approve')
            rec.state = 'draft'
            rec._send_email(
                'attendance_change_request.'
                'change_request_rtrnd_email_tmplt',
                None, 'draft', rec.id, 'attendance_change_request')

    def get_first_last_date(self, date):
        add_month = date + relativedelta(months=1, day=1)
        # add_date = add_month + relativedelta()
        last_date_s = add_month - relativedelta(days=1)
        first_date_s = last_date_s + relativedelta(day=1)
        return first_date_s, last_date_s

    @api.multi
    def check_existing_attendance(self, date_from, date_to):
        exist_attendance = ''
        for rec in self:
            date_from = str(date_from) + ' 00:00:00'
            date_to = str(date_to) + ' 23:59:59'
            att_rec = self.env['hr.attendance'].search(
                [('check_in', '>=', date_from),
                 ('check_out', '<=', date_to)])
            if att_rec:
                for att in att_rec:
                    exist_attendance += str(att.check_in) + ', '
                raise Warning(_("Attendance Record Alredy Exist for "
                                "Employee %s on date %s!") %
                              (rec.employee_id.name, exist_attendance))

    def check_monthly_change_request(self, first_date, last_date, date):
        vals = {}
        date_from = str(date) + ' 00:00:00'
        date_to = str(date) + ' 23:59:59'
        first_date = str(first_date) + ' 00:00:00'
        last_date = str(last_date) + ' 23:59:59'
        change_request_rec = \
            self.search([
                ('employee_id.id', '=', self.employee_id.id),
                ('date_from', '>=', date_from), ('date_to', '<=', date_to)
            ])
        change_request_rec_monthly = self.search([
            ('employee_id.id', '=', self.employee_id.id),
            ('date_from', '>=', first_date),
            ('date_to', '<=', last_date),
        ])
        vals.update({'change_request_rec': change_request_rec,
                     'change_request_rec_monthly': change_request_rec_monthly})
        return vals

    @api.multi
    @api.constrains('date_from', 'date_to')
    def _check_attendance_date(self):
        for rec in self:
            attendance_config_rec = self.env[
                'attendance.configuration'].search([], limit=1)
            date_from, date_to = rec.get_latest_date()
            if attendance_config_rec:
                per_day_config = attendance_config_rec.per_day_change_request
                per_month_config = attendance_config_rec.month_change_request
                if not rec.onsite:
                    date = datetime.strptime(date_from or date_to, DF)
                    first_date_s, last_date_s = rec.get_first_last_date(date)
                    first_date = str(first_date_s).split(' ')[0]
                    last_date = str(last_date_s).split(' ')[0]
                    vals = rec.check_monthly_change_request(
                        first_date, last_date, date_from)
                    change_request_rec = vals.get('change_request_rec')
                    change_request_rec_monthly = \
                        vals.get('change_request_rec_monthly')
                    if len(change_request_rec) > per_day_config:
                        raise ValidationError(
                            _('Please, You have the rights to create '
                              '%s requests per day for more information'
                              ' contact to HR Team.') % per_day_config)
                    if len(change_request_rec_monthly) > per_month_config:
                        raise ValidationError(
                            _('Please, You have the rights to create '
                              '%s requests per month for more information'
                              ' contact to HR Team.') % per_month_config)

    def get_latest_date(self):
        if self.permission:
            date_from = self.date_from.split(' ')[0]
            date_to = self.date_to.split(' ')[0]
        elif self.sign_in:
            date_from = self.date_from.split(' ')[0]
            date_to = self.date_from.split(' ')[0]
        elif self.sign_out:
            date_from = self.date_to.split(' ')[0]
            date_to = self.date_to.split(' ')[0]
        elif self.onsite:
            date_from = self.date_from.split(' ')[0]
            date_to = self.date_to.split(' ')[0]
        return date_from, date_to

    def get_attendance_rec(self):
        date_from, date_to = self.get_latest_date()
        date_from = str(date_from) + ' 00:00:00'
        date_to = str(date_to) + ' 23:59:59'
        att_rec = self.env['hr.attendance'].search(
            [('check_in', '>=', date_from),
             ('check_out', '<=', date_to)], limit=1)
        return att_rec

    def check_equal_date(self):
        date_from, date_to = self.get_latest_date()
        if date_from != date_to:
            raise exceptions.ValidationError(_('Date From and Date to are '
                                               'should be same.'))
        return True

    def check_earlier_time(self, date_from, date_to):
        if date_from and date_to and self.onsite:
            if date_to < date_from:
                raise exceptions.ValidationError(_(
                    '"Check Out" time cannot'
                    ' be earlier than "Check In" time.'))

    def get_date_time(self, date_from, date_to):
        time_from = str(date_from).split(' ')[1]
        date_from = str(date_from).split(' ')[0]
        time_to = str(date_to).split(' ')[1]
        date_to = str(date_to).split(' ')[0]
        return date_from, date_to, time_from, time_to

    def submit_sign_in(self):
        context = dict(self._context)
        if context.get('sign_in'):
            raise Warning(_('Please make sure your date from is smaller than '
                            'Attendance check out'))
        elif context.get('sign_out'):
            raise Warning(_('Please make sure your date to is bigger than '
                            'Attendance check in'))

    @api.multi
    def sent_for_review(self):
        """
        employee change request send to immidiate manager
        :return:
        """
        for rec in self:
            rec.check_earlier_time(rec.date_from, rec.date_to)
            if rec.date_from and rec.date_to and rec.permission:
                rec.check_equal_date()
                rec._send_email(
                    'attendance_change_request.'
                    'change_request_mngr_email_tmplt',
                    None, 'for_review',
                    rec.id, 'attendance_change_request')
            elif rec.onsite:
                date_from, date_to, time_from, time_to = rec.get_date_time(
                    rec.date_from, rec.date_to)
                rec.check_existing_attendance(date_from, date_to)
                date_from_d = datetime.strptime(date_from, DF)
                date_to_d = datetime.strptime(date_to, DF)
                diff_days = int((date_to_d - date_from_d).days) + 1
                if diff_days > 1:
                    for single_date in [d for d in (date_from_d + timedelta(
                            n) for n in range(diff_days)) if d <= date_to_d]:
                        start_date = \
                            str(single_date).split(' ')[0] + ' ' + time_from
                        end_date = \
                            str(single_date).split(' ')[0] + ' ' + time_to
                        child_rec = self.create({
                            'active': True,
                            'employee_id': self.employee_id.id,
                            'date': str(single_date).split(' ')[0],
                            'date_from': start_date,
                            'date_to': end_date,
                            'parent_id': rec.id,
                            'state': 'for_review',
                            'onsite': True,
                            'change_reason_id': rec.change_reason_id.id,
                        })
                        rec._send_email(
                            'attendance_change_request.'
                            'change_request_mngr_email_tmplt',
                            None, 'for_review',
                            child_rec.id, 'attendance_change_request')
                    rec.active = False
                else:
                    rec._send_email(
                        'attendance_change_request.'
                        'change_request_mngr_email_tmplt',
                        None, 'for_review',
                        rec.id, 'attendance_change_request')
                    rec.state = 'for_review'
            else:
                rec._send_email(
                    'attendance_change_request.'
                    'change_request_mngr_email_tmplt',
                    None, 'for_review',
                    rec.id, 'attendance_change_request')
                rec.state = 'for_review'

    @api.multi
    def sent_for_hr_approval(self):
        """
        immideate manager agreed and send to hr manager
        HR Approval.
        :return: True
        """
        for rec in self:
            rec._check_user_permissions('approve')
            rec.state = 'hr_review'
            rec._send_email(
                'attendance_change_request.'
                'change_request_hr_email_tmplt',
                None, 'hr_review', rec.id, 'attendance_change_request')
        return True

    def create_attendance_record(self, date_from, date_to):
        attendance_obj = self.env['hr.attendance']
        attendance_obj.create({'employee_id': self.employee_id.id,
                               'date':
                                   str(date_from).split(' ')[
                                       0],
                               'check_in': date_from,
                               'check_out': date_to,
                               'manual_attendance': True,
                               'attendance_change_request_ids': [
                                   (4, self.id)]})
        return True

    def get_diff_hours(self, date_from, date_to):
        diff_h, diff_m, diff_s = 0, 0, 0
        date_from_d = \
            datetime.strptime(date_from,
                              DEFAULT_SERVER_DATETIME_FORMAT)
        date_to_d = \
            datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
        diff_hours = date_to_d - date_from_d
        if diff_hours:
            diff_h = int(str(diff_hours).split(':')[0])
            diff_m = int(str(diff_hours).split(':')[1])
            diff_s = int(str(diff_hours).split(':')[2])
        return diff_h, diff_m, diff_s

    @api.one
    def check_permission_change_request(self, attendance_rec, date_from,
                                        date_to):
        diff_h, diff_m, diff_s = self.get_diff_hours(date_from, date_to)
        if attendance_rec and date_from >= attendance_rec.check_out:
            record_date_to = datetime.strptime(
                attendance_rec.check_out,
                DEFAULT_SERVER_DATETIME_FORMAT)
            diff_date_to = record_date_to + timedelta(hours=diff_h,
                                                      minutes=diff_m,
                                                      seconds=diff_s)
            attendance_rec.write(
                {'attendance_change_request_ids': [(4, self.id)],
                 'check_out': diff_date_to})
        if attendance_rec and date_from < \
                attendance_rec.check_in and date_to <= \
                attendance_rec.check_in:
            record_date_from = \
                datetime.strptime(attendance_rec.check_in,
                                  DEFAULT_SERVER_DATETIME_FORMAT)
            diff_date = \
                record_date_from - timedelta(
                    hours=diff_h, minutes=diff_m, seconds=diff_s)
            attendance_rec.write(
                {'attendance_change_request_ids': [(4, self.id)],
                 'check_in': diff_date})

    @api.multi
    def attendance_change_approved(self, attendance_rec):
        if self.permission:
            self.check_permission_change_request(attendance_rec,
                                                 self.date_from,
                                                 self.date_to)
        # if late in
        if self.sign_in:
            attendance_rec.write(
                {'check_in': self.date_from,
                 'status': 'Attendance Updated(Sign in)',
                 'attendance_change_request_ids': [(4, self.id)]})
        # if early out
        if self.sign_out:
            attendance_rec.write(
                {'check_out': self.date_to,
                 'status': 'Attendance Updated(Sign out)',
                 'attendance_change_request_ids': [(4, self.id)]})
        self.write({'state': 'approved'})
        self._send_email(
            'attendance_change_request.'
            'change_request_aprvd_email_tmplt',
            None, 'approved', self.id, 'attendance_change_request')
        # if self.attendance_id:
        #     self.state = 'approved'
        #     self._send_email(
        #         'attendance_change_request.'
        #         'change_request_aprvd_email_tmplt',
        #         None, 'approved', self.id, 'attendance_change_request')
        # else:
        #     self.state = 'waiting_for_attendnace'
        #     self._send_email(
        #         'attendance_change_request.'
        #         'change_request_waiting_for_attendance_email_tmplt',
        #         None, 'approved', self.id, 'attendance_change_request')

    @api.multi
    def sent_for_review(self):
        """
        employee change request send to immidiate manager
        :return:
        """
        for rec in self:
            rec.check_earlier_time(rec.date_from, rec.date_to)
            if rec.date_from and rec.date_to and rec.permission:
                rec.check_equal_date()
                rec._send_email(
                    'attendance_change_request.'
                    'change_request_mngr_email_tmplt',
                    None, 'for_review',
                    rec.id, 'attendance_change_request')
            elif rec.onsite:
                date_from, date_to, time_from, time_to = rec.get_date_time(
                    rec.date_from, rec.date_to)
                rec.check_existing_attendance(date_from, date_to)
                date_from_d = datetime.strptime(date_from, DF)
                date_to_d = datetime.strptime(date_to, DF)
                diff_days = int((date_to_d - date_from_d).days) + 1
                if diff_days > 1:
                    for single_date in [d for d in (date_from_d + timedelta(
                            n) for n in range(diff_days)) if d <= date_to_d]:
                        start_date = \
                            str(single_date).split(' ')[0] + ' ' + time_from
                        end_date = \
                            str(single_date).split(' ')[0] + ' ' + time_to
                        child_rec = self.create({
                            'active': True,
                            'employee_id': self.employee_id.id,
                            'date': str(single_date).split(' ')[0],
                            'date_from': start_date,
                            'date_to': end_date,
                            'parent_id': rec.id,
                            'state': 'for_review',
                            'onsite': True,
                            'change_reason_id': rec.change_reason_id.id,
                        })
                        rec._send_email(
                            'attendance_change_request.'
                            'change_request_mngr_email_tmplt',
                            None, 'for_review',
                            child_rec.id, 'attendance_change_request')
                    rec.active = False
                else:
                    rec._send_email(
                        'attendance_change_request.'
                        'change_request_mngr_email_tmplt',
                        None, 'for_review',
                        rec.id, 'attendance_change_request')
                    rec.state = 'for_review'
            else:
                rec._send_email(
                    'attendance_change_request.'
                    'change_request_mngr_email_tmplt',
                    None, 'for_review',
                    rec.id, 'attendance_change_request')
                rec.state = 'for_review'

    @api.multi
    def verify_attendance(self):
        for rec in self:
            rec.state = 'approved'

    @api.onchange('date_from', 'date_to', 'change_reason_id')
    def onchange_attendance_id(self):
        """
        onchange attendance id
        :return:
        """
        if self.sign_in:
            self.date_to = False
        elif self.sign_out:
            self.date_from = False
