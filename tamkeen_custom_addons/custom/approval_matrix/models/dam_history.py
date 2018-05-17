from odoo import models, fields, api
from dam_manage import LEVEL


class DamConfHistory(models.Model):
    _name = 'dam.conf.history'

    @api.multi
    def _get_current_status(self):
        """
        get current state from the record.
        :return:
        """
        for rec in self:
            for history_line_rec in rec.history_line_ids:
                if history_line_rec.state == 'open':
                    if history_line_rec.rejected:
                        rec.current_status = 'Reject'
                    else:
                        rec.current_status = \
                            history_line_rec.dam_conf_line_id.name.name

    name = fields.Char('Reference')
    code = fields.Char('Code')
    object = fields.Many2one('ir.model', 'Object')
    history_line_ids = fields.One2many('dam.conf.history.line',
                                       'dam_conf_id', 'Approval Line')
    current_status = fields.Char('Current State',
                                 store=True, compute=_get_current_status)


class DamConfHistoryLine(models.Model):
    _name = 'dam.conf.history.line'

    name = fields.Selection(LEVEL, 'Levels')
    seq = fields.Integer('Sequence')
    user_ids = fields.Many2many('res.users', 'del_users_rel', 'h_id', 'u_id',
                                string='Allowed Approve User')
    approve_by_user_id = fields.Many2one('res.users', string='Approved By')
    assigned_time = fields.Datetime(string='Assigned Time')
    approve_time = fields.Datetime(string='Approve Time')
    bypass = fields.Boolean(string='Allow Delegation')
    bypass_user_ids = fields.Many2many('res.users', 'del_bypass_users_rel',
                                       'bypass_h_id', 'bypass_u_id',
                                       string='Allowed Delegate User')
    state = fields.Selection([('draft', 'Draft'),
                              ('open', 'Waiting For Approval'),
                              ('approved', 'Approved')], default='draft')
    dam_conf_id = fields.Many2one('dam.conf.history', 'History Id')
    dam_conf_line_id = fields.Many2one('dam.conf.line', 'Dam Conf Line')
    rejected = fields.Boolean('Rejected')
