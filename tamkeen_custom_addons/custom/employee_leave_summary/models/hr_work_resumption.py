# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from datetime import datetime, timedelta
import math
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


class WorkResumption(models.Model):
    _name = 'work.resumption'
    _description = 'Hr Leave Work Resumption'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.depends('actual_number_of_leave_days', 'number_of_leave_days')
    def get_diff_days_leaves(self):
        """
        :return:
        """
        for rec in self:
            diff_days = \
                rec.actual_number_of_leave_days - rec.number_of_leave_days
            rec.diff_days_leaves = diff_days

    @api.depends('actual_date_from', 'actual_date_to')
    def get_actual_number_of_leave_days(self):
        """
        :return:
        """
        holiday_obj = self.env['hr.holidays.public']
        for rec in self:
            get_day = 0.00
            ph_days = 0.00
            r_days = 0.00
            ph_days_holidays, r_days_holidays = 0.0, 0.0
            if rec.actual_date_to and rec.actual_date_from:
                start_date = datetime.strptime(rec.actual_date_from,
                                               '%Y-%m-%d').date()
                end_date = datetime.strptime(rec.actual_date_to,
                                             '%Y-%m-%d').date()
                if end_date >= start_date:
                    diff_date = end_date - start_date
                    get_day = (diff_date.days) + 1
                if rec.employee_id and rec.employee_id.contract_id \
                        and rec.employee_id.contract_id.working_hours:
                    ex_rd = rec.holiday_status_id.ex_rest_days
                    ex_ph = rec.holiday_status_id.ex_public_holidays
                    rest_days = rec.employee_id.contract_id. \
                        working_hours.get_rest_days()
                    dt = start_date
                    dt_to = end_date
                    if (dt_to and dt) and (dt <= dt_to):
                        td = dt_to - dt
                        diff_day = td.days + float(td.seconds) / 86400
                        number_of_days_temp = round(math.floor(diff_day)) + 1
                    else:
                        number_of_days_temp = 0

                    count_days = number_of_days_temp
                    next_dt = dt
                    while count_days > 0:
                        public_holiday = holiday_obj.is_public_holiday(next_dt)
                        if public_holiday and ex_ph:
                            ph_days += 1
                        # public_holiday = (public_holiday and ex_ph)
                        rest_day = (next_dt.weekday() in rest_days and ex_rd)
                        if rest_day:
                            r_days += 1
                        next_dt += timedelta(days=+1)
                        count_days -= 1
                    reported_date = datetime.strptime(rec.date_resumption,
                                                      OE_DATEFORMAT)
                    count_days_holidays = number_of_days_temp
                    if rec.date_resumption and reported_date.weekday() \
                            == 6 and \
                            not rec.holiday_status_id.ex_rest_days:
                        date_resumption = end_date
                        while count_days_holidays > 0:
                            date_resumption -= timedelta(days=+1)
                            public_holiday = holiday_obj.is_public_holiday(
                                date_resumption)
                            rest_day = (
                                date_resumption.weekday() in rest_days)
                            if public_holiday and ex_ph:
                                ph_days_holidays += 1
                            if rest_day:
                                r_days_holidays += 1
                            if not public_holiday and not rest_day:
                                break
                            count_days_holidays -= 1
            rec.actual_number_of_leave_days = (get_day - r_days) - ph_days
            rec.actual_number_of_leave_days = \
                (rec.actual_number_of_leave_days - r_days_holidays
                 ) - ph_days_holidays

    def get_last_working_date(self, date, rest_days):
        for index in range(date.weekday()):
            previous_date = date - timedelta(days=1)
            if previous_date.weekday() in rest_days:
                date = date - timedelta(days=1)
            else:
                break
        date = date - timedelta(days=1)
        return date

    @api.onchange('date_resumption')
    def onchange_date_resumption(self):
        """
        on change of date_resumption, set actual_date_to.
        :return:
        """
        holiday_obj = self.env['hr.holidays.public']
        if self.date_resumption:
            rest_days = self.employee_id.contract_id. \
                working_hours.get_rest_days()
            reported_date = datetime.strptime(self.date_resumption,
                                              OE_DATEFORMAT)
            if reported_date.weekday() in rest_days:
                raise Warning(_('Please, You are not allowed to select an '
                                'off day, For more information contact the HR '
                                'Team.'))
            if self.date_resumption < self.actual_date_from:
                raise Warning(_('Reported to work date must be bigger'
                                'than Leave Start Date'))
            if (holiday_obj.is_public_holiday(reported_date.date())) and \
                    self.holiday_status_id.ex_public_holidays:
                raise Warning(
                    _('Please, You are not allowed to select a '
                      'public holiday,'
                      ' please choose another day.'))
            date_resumption = fields.Date.from_string(self.date_resumption)
            last_working_date = self.\
                get_last_working_date(date_resumption, rest_days)
            # date_resumption -= relativedelta(days=1)
            self.actual_date_to = last_working_date

    @api.multi
    def _check_currect_user(self):
        """
        Check current user or not.
        :return:
        """
        for rec in self:
            if rec.create_uid.id == self._uid:
                rec.is_currect_user = True
            else:
                rec.is_currect_user = False

    @api.multi
    def write(self, vals):
        for rec in self:
            rest_days = rec.employee_id.contract_id. \
                working_hours.get_rest_days()
            if vals.get('date_resumption'):
                date_resumption = \
                    fields.Date.from_string(vals.get('date_resumption'))
                date_resumption = self.get_last_working_date(date_resumption,
                                                             rest_days)
                # date_resumption -= relativedelta(days=1)
                vals.update({'actual_date_to': date_resumption})
        return super(WorkResumption, self).write(vals)

    name = fields.Char('Name')
    employee_id = fields. \
        Many2one('hr.employee', string='Employee')
    employee_company_id = fields.Char('Employee Company Id',
                                      related='employee_id.f_employee_no')
    state = fields.Selection([('draft', 'To Submit'),
                              ('cancel', 'Cancelled'),
                              ('confirm', 'Manager Approval'),
                              ('validate1', 'HR Approval'),
                              ('validate2', 'Senior HR Approve'),
                              ('vp', 'VP Approval'),
                              ('ceo', 'CEO Approval'),
                              ('refuse', 'Refused'),
                              ('validate', 'Approved')],
                             string='Status', track_visibility='onchange',
                             copy=False, default='draft')

    date_from = fields.Date('Leave Duration')
    date_to = fields.Date('Leave Duration')
    # number_of_leave_days = fields.Float('Number od Leave Days',
    #                                     compute='get_number_of_leave_days')
    number_of_leave_days = fields.Float(string='Number of Leave Days')
    date_resumption = fields.Date('Reported to work on ')
    actual_date_from = fields.Date('Actual Leave Duration')
    actual_date_to = fields.Date('Actual Leave Duration')
    actual_number_of_leave_days = fields. \
        Float('Actual Number of Leave Days',
              compute='get_actual_number_of_leave_days')
    comment = fields.Text('Comment')
    diff_days_leaves = fields.Float(compute='get_diff_days_leaves')
    hr_holiday_id = fields.Many2one('hr.holidays', 'Leave Request')
    is_currect_user = fields.Boolean('is Currect User',
                                     compute='_check_currect_user')
    holiday_status_id = fields.Many2one(
        'hr.holidays.status', string='Leave Type')
    skip_notification = fields.Boolean(string='Skip Notification')

    @api.model
    def create(self, vals):
        """
        ovride create method
        :param vals: dictonary
        :return:
        """
        vals['name'] = self.env['ir.sequence'].next_by_code('work.resumption')
        return super(WorkResumption, self).create(vals)

    @api.multi
    def _set_email_template_context(self):
        ir_model_data = self.env['ir.model.data']
        context = dict(self._context)
        display_link = False
        base_url = self.env['ir.config_parameter'].\
            get_param('web.base.url.static')
        action_id = False
        window_action_id = window_action_ref = False
        window_action_ref = 'employee_leave_summary.action_hr_work_resumption'
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
            'model': 'work.resumption'
        })
        return context

    @api.multi
    def action_confirm(self):
        """
        Request submit for manager approval.
        :return:
        """
        template_obj = self.env['mail.template']
        ir_model_data = self.env['ir.model.data']
        for rec in self:
            if rec.actual_date_to < rec.actual_date_from:
                raise Warning(
                    _('The Actual date from must'
                      ' be anterior to the Actual date to'))
            try:
                template_id = ir_model_data.get_object_reference(
                    'employee_leave_summary',
                    'email_template_work_resumption_approve_to_manager')[1]
            except ValueError:
                template_id = False
            if template_id and not rec.skip_notification:
                template_rec = template_obj.browse(template_id)
                context = self._set_email_template_context()
                template_rec.with_context(context).send_mail(
                    self.id, force_send=False)
            rec.state = 'confirm'

    @api.multi
    def action_manager_approve(self):
        """
        Request Validate by Manager.
        :return:
        """
        template_obj = self.env['mail.template']
        ir_model_data = self.env['ir.model.data']
        for rec in self:
            rec.write({'state': 'validate1'})
            try:
                template_id = ir_model_data.get_object_reference(
                    'employee_leave_summary',
                    'email_template_work_resumption_approve_by_manager')[1]
            except ValueError:
                template_id = False
            if template_id and not rec.skip_notification:
                template_rec = template_obj.browse(template_id)
                context = self._set_email_template_context()
                template_rec.with_context(context).send_mail(
                    self.id, force_send=False)
        return True

    @api.multi
    def action_vp_approve(self):
        """
        Request Validate by VP.
        :return:
        """
        for rec in self:
            if rec.hr_holiday_id.holiday_status_id.hr_appr:
                rec.state = 'validate1'
            elif rec.hr_holiday_id.holiday_status_id.ceo_number\
                    > 0 and rec.hr_holiday_id.holiday_status_id.ceo_number\
                    <= rec.hr_holiday_id.real_days:
                rec.state = 'ceo'
            else:
                rec.state = 'validate'
                rec.hr_holiday_id.write({'work_resumption_done': True})
        return True

    @api.multi
    def action_hr_approval(self):
        """
        :return:
        """
        template_obj = self.env['mail.template']
        ir_model_data = self.env['ir.model.data']

        for rec in self:
            rec.state = 'validate'
            rec.hr_holiday_id.write({'work_resumption_done': True})
            curr_remaining_leaves = 0.0
            if rec.hr_holiday_id.max_allowed_days_value \
                    or rec.actual_number_of_leave_days:
                curr_remaining_leaves = \
                    rec.hr_holiday_id.max_allowed_days_value \
                    - rec.actual_number_of_leave_days
            if rec.hr_holiday_id:
                self.env['hr.holidays'].browse(rec.hr_holiday_id.id).write(
                    {'ori_leave_start': rec.date_from,
                     'ori_leave_end': rec.date_to,
                     'date_from': rec.actual_date_from,
                     'date_to': rec.actual_date_to,
                     'real_days_value': rec.actual_number_of_leave_days,
                     'actual_number_days': rec.number_of_leave_days,
                     'state': 'validate',
                     'curr_remaining_leaves_value': curr_remaining_leaves,
                     'working_days_value': rec.actual_number_of_leave_days,
                     'total_days_value': rec.actual_number_of_leave_days,
                     'number_of_days_temp': rec.actual_number_of_leave_days,
                     'final_approval_user_id': self.env.user.id,
                     'final_approval_date': datetime.now().strftime(
                         OE_DTFORMAT),
                     }
                )
            try:
                template_id = ir_model_data.get_object_reference(
                    'employee_leave_summary',
                    'email_template_work_resumption_approve_by_hr_manager')[1]
            except ValueError:
                template_id = False
            if template_id and not rec.skip_notification:
                template_rec = template_obj.browse(template_id)
                context = self._set_email_template_context()
                template_rec.with_context(context).send_mail(
                    self.id, force_send=False)
        return True

    @api.multi
    def action_senior_hr_approval(self):
        """
        :return:
        """
        for rec in self:
            if rec.hr_holiday_id.holiday_status_id.ceo_number\
                    > 0 and rec.hr_holiday_id.holiday_status_id.ceo_number <=\
                    rec.hr_holiday_id.real_days:
                rec.state = 'ceo'
            else:
                rec.state = 'validate'
                rec.hr_holiday_id.write({'work_resumption_done': True})
        return True

    @api.multi
    def action_ceo_approval(self):
        """
        :return:
        """
        for rec in self:
            rec.state = 'validate'
            rec.holiday_status_id.write({'work_resumption_done': True})
        return True

    @api.multi
    def reset_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
