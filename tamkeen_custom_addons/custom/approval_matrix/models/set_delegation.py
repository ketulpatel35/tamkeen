from odoo import models, fields, api, _
from odoo.exceptions import Warning
import logging
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DTFORMAT

_logger = logging.getLogger(__name__)


class SetDelegateUser(models.Model):
    _name = 'set.delegate.user'
    _rec_name = 'employee_id'

    all_object = fields.Boolean('Apply for All Object', default=True)
    allowed_object_ids = fields.Many2many('dam.conf', 'tbl_set_delegate_user',
                                          'set_del_id', 'templates_id',
                                          'Approval Templates')

    state = fields.Selection([('draft', 'Draft'),
                              ('send_for_approval', 'Send for Approval'),
                              ('approved', 'Approved'),
                              ('cancel', 'Cancel'), ], default='draft')
    current_user = fields.Many2one('res.users', 'Current User',
                                   default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  default=lambda self:
                                  self.env['hr.employee'].search([
                                      ('user_id', '=', self._uid)],
                                      limit=1) or False)
    delegate_user = fields.Many2one('res.users', 'Delegate User')
    date_form = fields.Date('Date From')
    date_to = fields.Date('Date To')
    immediate_manager = fields.Many2one('hr.employee',
                                        related='employee_id.parent_id',
                                        string='Immediate Manager')

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        if vals.get('date_form') and vals.get('date_to'):
            date_from = datetime.strptime(vals.get('date_form'),
                                          DTFORMAT).date()
            date_to = datetime.strptime(vals.get('date_to'), DTFORMAT).date()
            if date_to < date_from:
                raise Warning(_('Date From must be Greter then Date to!'))
        return super(SetDelegateUser, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        :param vals:
        :return:
        """
        for rec in self:
            date_from = datetime.strptime(rec.date_form,
                                          DTFORMAT).date()
            date_to = datetime.strptime(rec.date_to, DTFORMAT).date()
            if vals.get('date_from'):
                date_from = datetime.strptime(vals.get('date_from'),
                                              DTFORMAT).date()

            if vals.get('date_to'):
                date_to = datetime.strptime(vals.get('date_to'),
                                            DTFORMAT).date()
            if date_to < date_from:
                raise Warning(_('Date From must be Greter then Date to!'))
        return super(SetDelegateUser, self).write(vals)

    @api.multi
    def send_for_approval(self):
        """
        send for approval
        :return:
        """
        for rec in self:
            if not rec.immediate_manager:
                raise Warning(_('Employee has not Immediate Manager'))
            rec.state = 'send_for_approval'

    @api.multi
    def manager_approval(self):
        """
        :return:
        """
        for rec in self:
            templets_rec = self.env[('dam.conf')].search([])
            if not rec.all_object:
                if not rec.allowed_object_ids:
                    raise Warning(_('Please Select Object Templates for '
                                    'set Delegation.'))
                templets_rec = rec.allowed_object_ids
            for dam_conf_rec in templets_rec:
                for conf_line_rec in dam_conf_rec.conf_line_ids:
                    for stage_config_rec in conf_line_rec.stage_config_ids:
                        for multi_user_all_rec in \
                                stage_config_rec.multi_user_all_ids:
                            if multi_user_all_rec.allowed_user.id == \
                                    rec.current_user.id:
                                multi_user_all_rec.write(
                                    {'delegate_user': rec.delegate_user.id,
                                     'active_delegate': True,
                                     'allowed_bypass': True})
            rec.state = 'approved'

    @api.multi
    def cancel_approval(self):
        """
        :return:
        """
        for rec in self:
            templets_rec = self.env[('dam.conf')].search([])
            if not rec.all_object:
                if not rec.allowed_object_ids:
                    raise Warning(_('Please Select Object Templates for '
                                    'set Delegation.'))
                templets_rec = rec.allowed_object_ids
            for dam_conf_rec in templets_rec:
                for conf_line_rec in dam_conf_rec.conf_line_ids:
                    for stage_config_rec in conf_line_rec.stage_config_ids:
                        for multi_user_all_rec in \
                                stage_config_rec.multi_user_all_ids:
                            if multi_user_all_rec.allowed_user.id == \
                                    rec.current_user.id:
                                multi_user_all_rec.write(
                                    {'delegate_user': False,
                                     'active_delegate': False,
                                     'allowed_bypass': False})
            rec.state = "cancel"
