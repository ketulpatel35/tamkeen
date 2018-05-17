import time
from odoo import fields, api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError


class hr_infraction_category(models.Model):
    _name = 'hr.infraction.category'
    _description = 'Infraction Type'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')


class hr_infraction(models.Model):
    _name = 'hr.infraction'
    _description = 'Infraction'

    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Subject')
    date = fields.Date(string='Date', default=time.strftime(
        DEFAULT_SERVER_DATE_FORMAT))
    employee_id = fields.Many2one('hr.employee', string='Employee')
    category_id = fields.Many2one('hr.infraction.category', string='Category')
    action_ids = fields.One2many('hr.infraction.action', 'infraction_id',
                                 string='Actions')
    memo = fields.Text(string='Description')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('action', 'Actioned'), ('noaction',
                                                       'No Action')],
                             string='State',
                             default='draft')

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'confirm':
            return 'hr_infraction.mt_alert_infraction_confirmed'
        elif 'state' in init_values and self.state == 'action':
            return 'hr_infraction.mt_alert_infraction_action'
        elif 'state' in init_values and self.state == 'noaction':
            return 'hr_infraction.mt_alert_infraction_noaction'
        return super(hr_infraction, self)._track_subtype(init_values)

    @api.multi
    def do_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    @api.model
    def _needaction_domain_get(self):

        users_obj = self.env['res.users']

        domain = []
        if users_obj.has_group('hr.group_hr_manager'):
            domain = [('state', '=', 'confirm')]

        if len(domain) == 0:
            return False

        return domain

    @api.multi
    def unlink(self):
        for infraction in self:
            if infraction.state not in ['draft']:
                raise UserError('Infractions that have progressed beyond '
                                '"Draft" state may not be removed.')

        return super(hr_infraction, self).unlink()

    @api.onchange('category_id')
    def onchange_category(self):
        if self.category_id:
            self.name = self.category_id.name


ACTION_TYPE_SELECTION = [
    ('warning_verbal', 'Verbal Warning'),
    ('warning_letter', 'Written Warning'),
    ('transfer', 'Transfer'),
    ('suspension', 'Suspension'),
    ('dismissal', 'Dismissal'),
]


class hr_infraction_action(models.Model):
    _name = 'hr.infraction.action'
    _description = 'Action Based on Infraction'

    infraction_id = fields.Many2one('hr.infraction', string='Infraction',
                                    ondelete='cascade')
    type = fields.Selection(ACTION_TYPE_SELECTION, string='Type')
    memo = fields.Text(string='Notes')
    employee_id = fields.Many2one('hr.employee',
                                  related='infraction_id.employee_id',
                                  store=True, string='Employee')
    warning_id = fields.Many2one('hr.infraction.warning', string='Warning')
    transfer_id = fields.Many2one('hr.department.transfer', string='Transfer')

    _rec_name = 'type'

    @api.multi
    def unlink(self):
        for action in self:
            if action.infraction_id.state not in ['draft']:
                raise UserError('Actions belonging to Infractions not in '
                                '"Draft" state may not be removed.')
        return super(hr_infraction_action, self).unlink()


class hr_warning(models.Model):
    _name = 'hr.infraction.warning'
    _description = 'Employee Warning'

    name = fields.Char(string='Subject')
    date = fields.Date(string='Date Issued', default=time.strftime(
        DEFAULT_SERVER_DATE_FORMAT))
    type = fields.Selection([('verbal', 'Verbal'), ('written', 'Written')],
                            string='Type', default='written')
    action_id = fields.Many2one('hr.infraction.action', string='Action',
                                ondelete='cascade')
    infraction_id = fields.Many2one('hr.infraction',
                                    related='action_id.infraction_id',
                                    string='Infraction')
    employee_id = fields.Many2one('hr.employee',
                                  related='infraction_id.employee_id',
                                  string='Employee')

    @api.multi
    def unlink(self):

        for warning in self:
            if warning.action_id and warning.action_id.infraction_id.state \
                    not in ['draft']:
                raise UserError('Warnings attached to Infractions not in '
                                '"Draft" state may not be removed.')

        return super(hr_warning, self).unlink()


class hr_employee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    infraction_ids = fields.One2many('hr.infraction', 'employee_id',
                                     string='Infractions')
    infraction_action_ids = fields.One2many('hr.infraction.action',
                                            'employee_id',
                                            string='Disciplinary Actions')
