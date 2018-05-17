from datetime import datetime
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.exceptions import ValidationError, Warning


class hr_trainings(models.Model):
    _name = 'tamkeen.hr.trainings'
    _description = 'HR Employee Trainings Line'
    _rec_name = 'emp_line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def training_hr_reset(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'emp_self_services.action_hr_training_tree'
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
            'model': 'tamkeen.hr.trainings'
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
    def training_hr_rejected(self):
        self._send_email(
            'emp_self_services.hr_training_req_rejected', None,
            'reject', self.id, 'tamkeen_hr_trainings')
        view = self.env.ref(
            'emp_self_services.tamkeen_hr_training_reject_form_view')
        return {
            'name': _('Reject Reason'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tamkeen.hr.training.reject',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def training_hr_approved(self):
        for rec in self:
            rec.state = 'approved'
            self._send_email(
                'emp_self_services.hr_training_req_approved', None,
                'draft', self.id, 'tamkeen_hr_trainings')

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
                'emp_self_services.hr_training_req_send_to_hr', None,
                'hr_approval', self.id, 'tamkeen_hr_trainings')

    @api.depends('start_date', 'end_date')
    @api.multi
    def _get_number_of_days(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                s_date = datetime.strptime(rec.start_date, OE_DATEFORMAT)
                e_date = datetime.strptime(rec.end_date, OE_DATEFORMAT)
                if s_date and e_date:
                    days = (e_date - s_date).days + 1
                    rec.number_of_days = days

    @api.model
    def get_employee(self):
        employee = self.env['hr.employee']\
                       .search([('user_id', '=', self.env.uid)]) or False
        return employee

    def _get_default_trainings_req(self):
        str = '<p><b><font style="color: rgb(255, 0, 0);">To proceed, ' \
              'Kindly:\n' \
              '- Attach your experience certificate.\n' \
              ' Attach your GOSI letter that shown your length of service.\n' \
              '- Request will be approved and reviewed by HR.\n' \
              '-Information must be filled in English.</font></b></p>'
        return str

    emp_line = fields.Many2one('hr.employee',
                               string='Employee', default=get_employee, translate=True)
    source_name = fields.Char(string='Source Name', translate=True)
    title = fields.Char(string='Title', translate=True)
    start_date = fields.Date(string='Start Date', translate=True)
    end_date = fields.Date(string='End Date', translate=True)
    days_or_hours = fields.Selection([
        ('days', 'Days'),
        ('hours', 'Hours')], string='Days or Hours', default="days", translate=True)
    number_of_days = fields.\
        Integer(string='Number Of Days',
                compute='_get_number_of_days', translate=True, readonly=True)
    type = fields.\
        Selection([('membership', 'Membership'),
                   ('basic_soft', 'Basic/soft'),
                   ('specialized', 'Specialized'),
                   ('certified', 'Certified')], translate=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('hr_approval', 'HR Approval'),
                              ('approved', 'Approved'),
                              ('reject', 'Rejected'), ],
                             track_visibility='onchange', default='draft', translate=True)
    reject_reason = fields.Char('Reject Reason', readonly=True, translate=True)
    employee_company_id = fields.Char(related='emp_line.f_employee_no',
                                      string='Employee Company ID',
                                      readonly=True)
    requirements = fields.Text(string='Requirements', default=_get_default_trainings_req)
    active = fields.Boolean('Active', default=True)

    @api.multi
    def _check_date_training(self):
        for record in self:
            if record.start_date > record.end_date:
                return False
        return True

    _constraints = [
        (_check_date_training, 'The start date must be anterior to the end date.',
         ['start_date', 'end_date']),
    ]

    @api.multi
    def unlink(self):
        for data in self:
            if data.state != 'draft':
                raise ValidationError(
                    _('You may not a delete a record that is not'
                      ' in a "Draft" state'))
        return super(hr_trainings, self).unlink()

    @api.constrains('title', 'emp_line', 'source_name')
    def _name_job_unique(self):
        for rec in self:
            record = self.search([('emp_line', '=', rec.emp_line.id),
                                  ('title', '=', rec.title),
                                  ('id', '!=', rec.id),
                                  ('source_name', '=', rec.source_name)
                                  ])
            if record:
                raise ValidationError(
                    _('The training entry line should be unique per employee'))


class hr_training_rejection(models.Model):
    _name = 'tamkeen.hr.training.reject'
    _description = 'HR Employee training Rejection reason'


    name = fields.Char('Reason for reject', translate=True)

    @api.multi
    def reject_training(self):
        context = self._context or {}
        if context.get('active_id'):
            training_rec = self.env['tamkeen.hr.trainings'].browse(
                context.get('active_id'))
            training_rec.reject_reason = self.name
            training_rec.state = 'reject'
        return {'type': 'ir.actions.act_window_close'}
