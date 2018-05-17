# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, api, models, _
from odoo.exceptions import Warning
import time


class RequestTypes(models.Model):

    _name = "request.types"
    _description = "Requests Type"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Request Type')
    active = fields.\
        Boolean(string='Active',
                help="If the active field is set to false,"
                     " it will allow you to hide"
                     " the requests type without removing it.",
                default=True)
    double_validation = fields\
        .Boolean(string='Apply Double Validation',
                 help="When selected, the Requests for"
                      " this type require a second validation to be approved.")
    employee_id = fields.Many2one(
        'hr.employee',
        "Employee Approval",
        required=False)
    dep_validation = fields.Boolean(string='Manager Approval')
    hr_validation = fields.Boolean(string='HR Approval')


class request(models.Model):
    _name = 'request.general'
    _rec_name = 'name'
    _description = 'Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.one
    def copy(self, default=None):
        raise Warning('You can duplicate requests!')
        return super(request, self).copy(default=default)

    request_number = fields\
        .Char(string='Request Number',
              default=lambda self:
              self.env['ir.sequence'].next_by_code('request.general') or False)
    state = fields.Selection([
        ('draft', 'New'),
        ('dappr', 'Waiting Department Approval'),
        ('hrappr', 'Waiting HR Approval'),
        ('accepted', 'Approved'),
        ('cancelled', 'Refused'),
    ],
        string='Status',
        track_visibility='onchange',
        default="draft",
        help='When the request is created the status'
             ' is \'Draft\'.\n It is confirmed by the'
             ' user and request is sent to admin, the'
             ' status is \'Waiting Confirmation\'.\
                \nIf the admin accepts it, the status is \'Approved\'.')

    name = fields.Many2one(
        "request.types", string="Request Type", states={
            'draft': [
                ('readonly', False)], 'confirm': [
                ('readonly', False)]})

    description = fields.Text(string='Description')
    employee_id = fields\
        .Many2one('hr.employee',
                  string="Employee",
                  default=lambda self: self.env['hr.employee']
                  .search([('user_id', '=', self._uid)], limit=1) or False)
    user_id = fields.\
        Many2one(related='employee_id.user_id',
                 string='User', default=lambda self: self.env.user.id)

    department_id = fields\
        .Many2one(related='employee_id.department_id',
                  string='Department', store=True)
    manager_id = fields\
        .Many2one('hr.employee',
                  string='First Approval',
                  help='This area is automatically'
                       ' filled by the user who validate the leave')
    manager_id2 = fields\
        .Many2one('hr.employee',
                  string='Second Approval',
                  help='This area is automaticly filled by'
                       ' the user who validate the leave with'
                       ' second level (If Leave type need second validation)')
    double_validation = fields\
        .Boolean(related='name.double_validation',
                 string='Apply Double Validation')
    dep_validation = fields.Boolean(string='Department Approval')
    hr_validation = fields.Boolean(string='HR Manager Approval')
    date = fields.Date(string='Request Date',
                       default=lambda *a: time.strftime('%Y-%m-%d'))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_('You can only delete draft requests!'))
        return super(request, self).unlink()

    @api.multi
    def request_confirm(self):
        for requests in self:
            if requests.employee_id and requests.employee_id.parent_id.user_id:
                requests.message_subscribe_users(
                    user_ids=[requests.employee_id.parent_id.user_id.id])
        if requests.name.dep_validation:
            return self.write({'state': 'dappr'})
        if requests.name.dep_validation is False\
                and requests.name.hr_validation is True:
            return self.write({'state': 'hrappr'})
        if requests.name.dep_validation is False\
                and requests.name.hr_validation is False:
            return self.write({'state': 'hrappr'})

    @api.multi
    def request_accept(self):
        for requests in self:
            if requests.employee_id and \
                    requests.employee_id.parent_id and \
                    requests.employee_id.parent_id.user_id:
                requests.message_subscribe_users(
                    user_ids=[requests.employee_id.parent_id.user_id.id])
            manager = self.env['hr.employee'].\
                search([('user_id', '=', self._uid)], limit=1)
            if requests.name.hr_validation is True:
                self.write({'state': 'hrappr', 'manager_id': manager.id})
            if requests.name.hr_validation is False:
                self.write({'state': 'accepted', 'manager_id': manager.id})

    @api.multi
    def request_accept2(self):
        for rec in self:
            manager = self.env['hr.employee']\
                .search([('user_id', '=', self._uid)], limit=1)
            rec.write({'state': 'accepted', 'manager_id2': manager.id})

    @api.multi
    def request_canceled(self):
        obj_emp = self.env['hr.employee']
        manager = obj_emp.search([('user_id', '=', self._uid)], limit=1)
        for request in self:
            if request.state == 'dappr':
                request.write({'manager_id': manager.id, 'state': 'cancelled'})
            else:
                request.write({'manager_id2': manager.id,
                               'state': 'cancelled'})

    @api.multi
    def set_to_draft(self):
        for rec in self:
            rec.write({
                'state': 'draft',
                'manager_id': False,
                'manager_id2': False,
            })
