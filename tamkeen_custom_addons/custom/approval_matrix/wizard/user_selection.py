from odoo import models, api, fields, _
from odoo.exceptions import Warning
from datetime import datetime


class UserSelection(models.TransientModel):
    _name = "user.selection"

    conf_history_line_id = fields.Many2one('dam.conf.history.line',
                                           'conf History Line')
    user_id = fields.Many2one('res.users', 'Select User')

    @api.onchange('conf_history_line_id')
    def onchange_conf_history_line_id(self):
        """
        :return:
        """
        res = {}
        if self._context.get('user_ids'):
            res.update({'user_id': [
                ('id', 'in', self._context.get('user_ids'))]})
        return {'domain': res}

    def update_users_approvals(self):
        """
        :return:
        """
        if not self.user_id:
            raise Warning(_('Please Select at list one user for approval !'))
        rec_model = self._context.get('rec_model', False)
        rec_id = self._context.get('rec_id', False)
        if self.user_id and self.conf_history_line_id and rec_id and rec_model:
            self.conf_history_line_id.user_ids = [(6, 0, [self.user_id.id])]
            self.conf_history_line_id.write({'state': 'open',
                                             'assigned_time': datetime.now()})
            try:
                current_rec = self.env[rec_model].browse(rec_id)
                if current_rec:
                    current_rec.state = self.conf_history_line_id.name
                    conf_line_rec = self.conf_history_line_id.dam_conf_line_id
                    if conf_line_rec and conf_line_rec.stage_config_ids:
                        stage_config_id = conf_line_rec.stage_config_ids[0]
                        if stage_config_id.action_id:
                            self.env['dam.conf']._execute_server_action(
                                stage_config_id.action_id, rec_model, rec_id)
                    return {}
            except:
                return {}
