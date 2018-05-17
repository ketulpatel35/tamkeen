# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError,Warning


class hr_skill(models.Model):
    _name = 'hr.skill'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def get_employee(self):
        employee = \
            self.env['hr.employee'] \
                .search([('user_id', '=', self.env.uid)], limit=1) or False
        return employee

    def _get_default_skill_req(self):
        str = '<p><b><font style="color: rgb(255, 0, 0);">To proceed, Kindly:' \
              '- Team building skills.' \
              '- Excellent communication skills.' \
              '- Projects planning skills.</font></b></p>'
        return str

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)
    emp_line = fields.Many2one('hr.employee',
                        string='Employee', default=get_employee,
                        readonly=True, translate=True)

    employee_company_id = fields.Char(related='emp_line.f_employee_no',
                                      string='Employee Company ID',
                                      readonly=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('hr_approval', 'HR Approval'),
                              ('approved', 'Approved'),
                              ('reject', 'Rejected'), ],
                             track_visibility='onchange', default='draft',
                             translate=True)
    skill_level = fields.Selection([('basic', 'Basic'),
                                    ('advanced', 'Advanced'),
                                    ('expert', 'Expert')],
                                   track_visibility='onchange',
                                   translate=True, string='Skill Level')
    comment = fields.Text('Comments', translate=True)
    reject_reason = fields.Char('Reject Reason', readonly=True, translate=True)
    requirements = fields.Text(string='Requirements', default=_get_default_skill_req)
    active = fields.Boolean('Active', default=True)

    @api.multi
    def unlink(self):
        for data in self:
            if data.state != 'draft':
                raise ValidationError(
                    _('You may not a delete a record that is not'
                      ' in a "Draft" state'))
        return super(hr_skill, self).unlink()

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'hr_skill.open_view_skill_form'
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
            'model': 'hr.skill'
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
    def skill_hr_rejected(self):
        self._send_email(
            'hr_skill.hr_skill_req_rejected', None,
            'reject', self.id, 'hr_skill')
        view = self.env.ref(
            'hr_skill.tamkeen_hr_skill_reject_form_view')
        return {
            'name': _('Reject Reason'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tamkeen.hr.skill.reject',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def skill_hr_approved(self):
        for rec in self:
            rec.state = 'approved'
            self._send_email(
                'hr_skill.hr_skill_req_approved', None,
                'draft', self.id, 'hr_skill')

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
                'hr_skill.hr_skill_req_send_to_hr', None,
                'hr_approval', self.id, 'hr_skill')


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    skill_ids = fields\
        .One2many('hr.skill', 'emp_line',
                   string='Skills')

class hr_skill_rejection(models.Model):
    _name = 'tamkeen.hr.skill.reject'
    _description = 'HR Employee Skill Rejection reason'

    name = fields.Char('Reason for reject', translate=True)

    @api.multi
    def reject_skill(self):
        context = self._context or {}
        if context.get('active_id'):
            skill_rec = self.env['hr.skill'].browse(
                context.get('active_id'))
            skill_rec.reject_reason = self.name
            skill_rec.state = 'reject'
        return {'type': 'ir.actions.act_window_close'}