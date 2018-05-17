# -*- coding : utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http ://tiny.be>).
#
#    This program is free software : you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http ://www.gnu.org/licenses/>.
#
##############################################################################
import odoo
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import clean_action


class Meh_Action(odoo.addons.web.controllers.main.Action):

    @http.route('/web/action/load', type='json', auth="user")
    def load(self, action_id, additional_context=None):
        if action_id and action_id == 'hr_recruitment.create_job_simple':
            return super(
                Meh_Action,
                self).load(
                action_id,
                additional_context=additional_context)
        if additional_context and additional_context.get('active_model'):
            return super(
                Meh_Action,
                self).load(
                action_id,
                additional_context=additional_context)
        Actions = request.env['ir.actions.actions']
        value = False
        try:
            action_id = int(action_id)
        except ValueError:
            try:
                action = request.env.ref(action_id)
                assert action._name.startswith('ir.actions.')
                action_id = action.id
            except Exception:
                action_id = 0  # force failed read

        base_action = Actions.browse([action_id])
        if additional_context is None and\
                base_action.type == 'ir.actions.act_window':
            return super(
                Meh_Action,
                self).load(
                action_id,
                additional_context=additional_context)
        # read groups of current user
        user_groups = frozenset(request.env.user.groups_id)
        visible_menu_ids = []

        if base_action and base_action.type:
            ctx = {}
            action_type = base_action.type
            if action_type == 'ir.actions.report.xml':
                ctx.update({'bin_size': True})

            ctx = dict(request.context)
            action = request.env[action_type].\
                with_context(ctx).browse([action_id]).read()
            # get all menus that have reference to this action
            if action_type == 'ir.actions.act_window' and action and action[
                    0].get('id'):
                res = []
                # Current User Groups
                user_groups = frozenset(request.env.user.groups_id.ids)
                # # Take menu without group
                ir_menu_obj = request.env['ir.ui.menu']
                # all_all_menu_ids = set(ir_menu_obj.search([]).ids)
                all_menu_ids = set(ir_menu_obj.search([]).ids)
                general_allowed_menu_ids = list(
                    set(all_menu_ids))
                for menu in ir_menu_obj.browse(general_allowed_menu_ids):
                    if menu.action and menu.action.id == action_id:
                        res.append(menu.id)
                menu_ids = list(set(res))
                for menu_id in menu_ids:
                    cmenu_id = menu_id

                    while True:
                        cmenu_rec = ir_menu_obj.browse([cmenu_id])
                        parent_menu_id = cmenu_rec.\
                            parent_id.id if cmenu_rec.parent_id else False
                        if not parent_menu_id:
                            if cmenu_id in all_menu_ids:
                                visible_menu_ids.append(menu_id)
                            break
                        elif cmenu_id not in all_menu_ids:
                            break
                        cmenu_id = parent_menu_id
            # no groups_id === green light, user group has overlap with
            # groups_id, do_not_eval is only true in js button action call
            if ((action and action[0].get('groups_id', []) == []) and
                    visible_menu_ids) or action_type in\
                    ['ir.actions.report.xml', 'ir.actions.client']\
                    or not user_groups.isdisjoint(
                        set(action[0].get('groups_id', []))):
                value = clean_action(action[0])
        return value

# vim :expandtab :smartindent :tabstop=4 :softtabstop=4 :shiftwidth=4 :
