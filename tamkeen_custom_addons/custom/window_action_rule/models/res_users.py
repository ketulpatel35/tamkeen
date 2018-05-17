from odoo import api, models, fields


class ResGroups(models.Model):
    _inherit = 'res.groups'

    window_action_access = fields.Many2many('ir.actions.act_window',
                                            'ir_ui_window_action_group_rel',
                                            'group_id', 'window_action_id',
                                            'Window Actions')


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    user_id = fields.Many2one('res.users', 'Users')


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def _get_all_menu_actions(self):
        res = []
        user_groups = self[0].groups_id
        menu_obj = self.env['ir.ui.menu']
        menu_with_action_ids = menu_obj.search([('action', '!=', False)])
        general_menu_ids = menu_obj.search([('groups_id', '=', False)])
        general_allowed_menu_ids = list(
            set(menu_with_action_ids.ids + general_menu_ids.ids))
        for user_group in user_groups:
            for menu in menu_obj.browse(general_allowed_menu_ids):
                if menu.action:
                    menu_groups = menu.groups_id
                    if user_group in menu_groups or len(menu_groups) == 0:
                        res.append(menu.action.id)
        return res

    @api.multi
    def _get_user_window_action_ids(self):
        user_groups_action_ids, user_win_action_ids = [], []
        user_win_action_ids = self._get_all_menu_actions()
        user_groups = set(self.browse(self._uid).groups_id.ids)
        for rec in self:
            if user_groups:
                for group in user_groups:
                    user_groups_win_actions = set(
                        self.env['res.groups'].browse(
                            group).window_action_access)
                    if user_groups_win_actions:
                        for win_action in user_groups_win_actions:
                            user_groups_action_ids.append(win_action)
                if user_groups_action_ids:
                    for win_action_obj in self.env['ir.actions.act_window'].\
                            browse(user_groups_action_ids):
                        if win_action_obj:
                            user_win_action_ids.append(int(win_action_obj.id))
        all_window_action_ids = \
            self.env['ir.actions.act_window'].search([]).ids
        allowed_action_ids = \
            [set(all_window_action_ids), set(user_win_action_ids)]
        allowed_action_ids = \
            [set(action_id) for action_id in allowed_action_ids]
        rec.window_action_ids = self.env['ir.actions.act_window'].\
            browse(list(set.intersection(*allowed_action_ids)))

    window_action_ids = fields.One2many('ir.actions.act_window', 'user_id',
                                        compute=_get_user_window_action_ids,
                                        string='User Window Actions')
