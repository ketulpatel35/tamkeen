from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil import relativedelta as rdelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.exceptions import ValidationError, Warning


class hr_experiences(models.Model):
    _name = 'tamkeen.hr.experiences'
    _description = 'HR Employee Experiences Line'
    _rec_name = 'emp_line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    @api.multi
    def unlink(self):
        for data in self:
            if data.state != 'draft':
                raise ValidationError(
                    _('You may not a delete a record that is not'
                      ' in a "Draft" state'))
        return super(hr_experiences, self).unlink()

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'emp_self_services.action_hr_experience_tree'
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
            'model': 'tamkeen.hr.experiences'
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
    def experience_hr_rejected(self):
        self._send_email(
            'emp_self_services.hr_experience_req_rejected', None,
            'reject', self.id, 'tamkeen_hr_experiences')
        view = self.env.ref('emp_self_services.tamkeen_hr_experience_reject_form_view')
        return {
            'name': _('Reject Reason'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tamkeen.hr.experiences.reject',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
    @api.multi
    def experience_hr_reset(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def experience_hr_approved(self):
        for rec in self:
            rec.state = 'approved'
            self._send_email(
                'emp_self_services.hr_experience_req_approved', None,
                'draft', self.id, 'tamkeen_hr_experiences')

    @api.multi
    def check_attachment(self):
        for rec in self:
            ir_obj = self.env['ir.attachment']
            existing_attachement = ir_obj.search([
                ('res_id', '=', rec.id),
                ('res_model', '=', rec._name)])
            if not existing_attachement:
                raise Warning(_('You cannot submit the request without '
                                'attaching a document.\n For attaching a '
                                'document: press save then attach a '
                                'document.'))
            return True

    @api.multi
    def submit_to_hr(self):
        for rec in self:
            rec.check_attachment()
            rec.state = 'hr_approval'
            self._send_email(
                'emp_self_services.hr_experience_req_send_to_hr', None,
                'hr_approval', self.id, 'tamkeen_hr_experiences')

    @api.model
    def get_employee(self):
        employee =\
            self.env['hr.employee']\
                .search([('user_id', '=', self.env.uid)]) or False
        return employee

    @api.multi
    @api.depends('date_of_join', 'date_of_leave')
    def get_month_year(self):
        for rec in self:
            if rec.date_of_join and rec.date_of_leave:
                date_of_join =\
                    datetime.strptime(rec.date_of_join, OE_DATEFORMAT)
                date_of_leave =\
                    datetime.strptime(rec.date_of_leave, OE_DATEFORMAT)
                diff_of_date =\
                    rdelta.relativedelta(date_of_leave, date_of_join)
                if diff_of_date.years:
                    rec.period_month_year = str(diff_of_date.years) + \
                                            ' Year/s, '
                if rec.period_month_year and diff_of_date.months:
                    rec.period_month_year += str(diff_of_date.months) + \
                                             ' Month/s'
                elif not rec.period_month_year and diff_of_date.months:
                    rec.period_month_year = str(diff_of_date.months) + 'Month'

    def _get_default_experience_req(self):
        str = '<p><b><font style="color: rgb(255, 0, 0);">To proceed, ' \
              'Kindly:\n' \
              '- Attach your experience certificate.\n' \
              '- Attach your GOSI letter that shown your length of ' \
              'service.\n' \
              '- Request will be approved and reviewed by HR.\n' \
              '- Information must be filled in English.</font></b></p>'
        return str

    emp_line =\
        fields.Many2one('hr.employee',
                        string='Employee', default=get_employee, translate=True)
    company_name = fields.Char(string='Company Name', translate=True)
    job_name = fields.Char(string='Job Name', translate=True)
    date_of_join = fields.Date(string='Date of join', translate=True)
    date_of_leave = fields.Date(string='Date of Leave', translate=True)
    responsibility = fields.Text(string='Responsibility', translate=True)
    period = fields.Integer(compute='period_of_days',
                          string="Period by days",
                          store=True,
                          help="Total Days", translate=True)
    period_month_year = fields.Char(compute='get_month_year',
                                    string='Period by months and years', translate=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('hr_approval', 'HR Approval'),
                              ('approved', 'Approved'),
                              ('reject', 'Rejected'), ],
                             track_visibility='onchange', default='draft', translate=True)
    reject_reason = fields.Char('Reject Reason', readonly=True, translate=True)
    employee_company_id = fields.Char(related='emp_line.f_employee_no',
                                      string='Employee Company ID',
                                      readonly=True)
    requirements = fields.Text(string='Requirements', default=_get_default_experience_req)
    active = fields.Boolean('Active', default=True)
    _sql_constraints = [
        ('date_to_from_check', "CHECK (date_of_join <= date_of_leave)",
         "The start date must be anterior to the end date."),

        # ('name_employee_uniq', "UNIQUE(company_name, emp_line)",
        #  "The entry name should be unique per employee")
    ]


    @api.constrains('job_name', 'emp_line', 'company_name')
    def _name_job_unique(self):
        for rec in self:
            record = self.search([('emp_line', '=', rec.emp_line.id),
                                 ('job_name', '=',rec.job_name),
                                  ('id', '!=', rec.id),
                                  ('company_name', '!=', rec.company_name)])
            if record:
                raise ValidationError(
                    _('The experience entry line should be unique per '
                      'employee'))



    @api.onchange('date_of_join', 'date_of_leave')
    def onchange_date(self):
        # date_of_leave has to be greater than date_of_join
        if (self.date_of_join and self.date_of_leave) and \
                (self.date_of_join > self.date_of_leave):
            raise Warning(_('The start date must be anterior'
                            ' to the end date.'))

    @api.one
    @api.depends('date_of_join', 'date_of_leave')
    def period_of_days(self):
        days = 0
        if self.date_of_join and self.date_of_leave:
            date_of_join = datetime.strptime(self.date_of_join,
                                             '%Y-%m-%d')
            date_of_leave = datetime.strptime(self.date_of_leave,
                                              '%Y-%m-%d')
            period = date_of_leave - date_of_join
            days = period.days
        self.period = days



class hr_experiences_rejection(models.Model):
    _name = 'tamkeen.hr.experiences.reject'
    _description = 'HR Employee Experiences Rejection reason'


    name = fields.Char('Reason for reject', translate=True)

    @api.multi
    def reject_experience(self):
        context = self._context or {}
        if context.get('active_id'):
            exp_rec = self.env['tamkeen.hr.experiences'].browse(
                context.get('active_id'))
            exp_rec.reject_reason = self.name
            exp_rec.state = 'reject'
        return {'type': 'ir.actions.act_window_close'}
