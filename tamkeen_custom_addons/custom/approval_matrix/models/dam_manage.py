from odoo import models, api, fields, _
from odoo.exceptions import Warning
from datetime import datetime

LEVEL = [('l1', 'Level 1'), ('l2', 'Level 2'), ('l3', 'Level 3'),
         ('l4', 'Level 4'), ('l5', 'Level 5'), ('l6', 'Level 6'),
         ('l7', 'Level 7'), ('l8', 'Level 8'), ('l9', 'Level 9'),
         ('l10', 'Level 10')]


class DamLevels(models.Model):
    _name = 'dam.levels'

    code = fields.Char('Id', required="1")
    name = fields.Char('Name', required="1")
    levels = fields.Selection(LEVEL, 'Levels')


class DamConf(models.Model):
    _name = 'dam.conf'

    @api.model
    def get_state(self, model_name):
        """
        get stage from configuration.
        :return:
        """
        state = []
        if model_name:
            model_rec = self.env['ir.model'].search([
                ('model', '=', model_name)])
            if model_rec:
                conf_rec = self.search([('object', '=', model_rec.id)])
                if conf_rec:
                    if self._context and self._context.get(
                            'default_state', False):
                        default_state = False
                        for line_rec in conf_rec.conf_line_ids:
                            if not default_state:
                                default_state = line_rec.name.levels
                            if line_rec.default_state:
                                default_state = line_rec.name.levels
                        return default_state
                    for line_rec in conf_rec.conf_line_ids:
                        state.append(
                            (line_rec.name.levels, line_rec.name.name))
        return state

    @api.model
    def get_default_state(self, model_name):
        """
        :return: return default state or first state of line.
        """
        if model_name:
            default_state = self.with_context(
                {'default_state': True}).get_state(model_name)
            return default_state or ''

    @api.model
    def get_xml_view(self):
        """
        :return:
        """
        if self.object:
            parent_view_rec = self.env['ir.ui.view'].search([
                ('type', '=', 'form'), ('mode', '=', 'primary'),
                ('model', '=', self.object.model)])
            if parent_view_rec:
                return parent_view_rec
            else:
                raise Warning(_('No primary view found.'))

    def create_update_view_rec(self, parent_view_rec, data):
        """
        :return:
        """
        vals = {
            'name': self.object.model + '.dynamic',
            'model': self.object.model,
            'model_data_id': self.object.id,
            'inherit_id': parent_view_rec.id,
            'mode': 'extension',
            'active': True,
            'priority': 16,
            'arch_db': data,
            'type': 'form',
            'customize_show': False,
            'page': False
        }
        new_view_rec = self.env['ir.ui.view'].create(vals)
        return new_view_rec

    def get_create_view_data(self):
        """
        :return:
        """
        data = """<?xml version="1.0"?>
        <xpath expr="//header" position="inside">"""
        for btn_rec in self.conf_line_ids:
            # stage configuration record
            stage_config_rec = False
            is_reject = False
            add_reject_btn = False
            if btn_rec.stage_config_ids:
                stage_config_rec = btn_rec.stage_config_ids[0]
                is_reject = stage_config_rec.is_reject
                add_reject_btn = stage_config_rec.add_reject_btn
            if btn_rec.end_state:
                continue
            if not is_reject:
                attrs_data = \
                    {'invisible': [('state', '!=', str(btn_rec.name.levels))]}
                btn_string = btn_rec.name.name
                if stage_config_rec and stage_config_rec.name:
                    btn_string = stage_config_rec.name
                data += """\n<button class="oe_highlight o_form_invisible"
                clickable="True" context="{'btn_rec_id': %s}"
                name="action_set_next_stage" string='%s' attrs="%s"
                type="object"/>""" % (btn_rec.id, btn_string, attrs_data)
                if add_reject_btn:
                    data += \
                        """\n<button class="oe_highlight o_form_invisible"
                        clickable="True" name="action_set_next_stage"
                        context="{'btn_rec_id': %s, 'reject': True}"
                        string='%s' states="%s" type="object"/>""" % (
                            btn_rec.id, 'Reject', btn_rec.name.levels)
        data += """</xpath>"""
        self.btn_data = data.lstrip()
        if not self.xml_view_id:
            parent_view_rec = self.get_xml_view()
            view_rec = self.create_update_view_rec(parent_view_rec,
                                                   data.lstrip())
            if view_rec:
                self.xml_view_id = view_rec.id
        else:
            self.xml_view_id.write({
                'arch_db': data.lstrip()
            })

    @api.model
    def get_dam_conf_data(self, rec_model):
        """
        :return:
        """
        data = []
        conf_rec = self.env['dam.conf'].search([('object', '=', rec_model)])
        if not conf_rec:
            return data
        for rec in conf_rec.conf_line_ids:
            # user_id = rec.user_id and rec.user_id.id or False
            # user_bypass_id = \
            #     rec.user_bypass_id and rec.user_bypass_id.id or False
            if rec.stage_config_ids:
                stage_config_id = rec.stage_config_ids[0]
                user_bypass_ids = []
                user_ids = []
                for multi_user_all_rec in stage_config_id.multi_user_all_ids:
                    if multi_user_all_rec.allowed_user:
                        user_ids.append(
                            (4, multi_user_all_rec.allowed_user.id))
                    if multi_user_all_rec.allowed_bypass and \
                            multi_user_all_rec.delegate_user:
                        user_bypass_ids.append(
                            (4, multi_user_all_rec.delegate_user.id))
            data.append((0, 0, {'seq': rec.sequence,
                                'name': rec.name.levels,
                                'user_ids': user_ids,
                                'bypass_user_ids': user_bypass_ids,
                                'dam_conf_line_id': rec.id,
                                }))
        return data

    def get_history_record(self, rec_model, rec_id):
        """
        get dam conf history record, create new if not exist.
        :return:
        """
        model = self.env['ir.model'].search([('model', '=', rec_model)])
        if not model:
            raise Warning(
                _('requested model %s dose not exist.') % (rec_model))
        history_rec = self.env['dam.conf.history'].search([
            ('code', '=', rec_id), ('object', '=', model.id)])
        if history_rec and history_rec.id:
            return history_rec
        else:
            name = self._context.get('source_doc', '')
            history_rec = self.env['dam.conf.history'].create(
                {'name': name, 'code': int(rec_id), 'object': model.id})
        line_data = self.get_dam_conf_data(rec_model)
        if line_data:
            history_rec.history_line_ids = line_data
        return history_rec

    @api.model
    def check_bypass_user_allocation(self, history_line_rec):
        """
        :param history_line_rec:
        :return:
        """
        current_user = self.env.user
        deligate_users = history_line_rec.bypass_user_ids.ids
        if len(deligate_users) == 1:
            if deligate_users[0] != current_user.id:
                raise Warning(_('You are not allowed to approve/reject this '
                                'document. Please contact system admin'))
            else:
                return True
        elif len(deligate_users) > 1:
            raise Warning(_('Select only 1 User for Approval Process.'))

    @api.model
    def check_user_allocation(self, history_line_rec):
        """
        check user leval validation.
        :param history_line_rec: Delegation line record.
        :return:
        """
        # Check User Allowed
        current_user = self.env.user
        allowed_users = history_line_rec.user_ids.ids
        if len(allowed_users) == 1:
            if allowed_users[0] != current_user.id:
                check_bypass = self.check_bypass_user_allocation(
                    history_line_rec)
                return check_bypass
            else:
                return True
        elif len(allowed_users) > 1:
            raise Warning(_('Select only 1 User for Approval Process.'))
        return True

    @api.model
    def _execute_server_action(self, action_rec, rec_model, rec_id):
        """
        :param action_id: server action id that should be call
        :param rec_model: object record
        :param rec_id: record id
        :return:
        """
        if action_rec:
            action_rec.with_context({'active_id': rec_id,
                                     'active_ids': [rec_id],
                                     'active_model': rec_model}).run()

    @api.model
    def update_current_record(self, rec_model, rec_id, line_rec, history_rec):
        """
        :param rec_model:
        :param rec_id:
        :param line_rec:
        :param history_rec:
        :return:
        """
        sequence = [rec.seq for rec in history_rec.history_line_ids]
        current_seq = line_rec.seq
        current_index = sequence.index(current_seq)
        next_index = current_index + 1
        total_line = len(history_rec.history_line_ids)
        next_line_rec = False
        if next_index < total_line:
            next_line_rec = history_rec.history_line_ids[next_index]
        line_rec.write({
            'state': 'approved',
            'approve_by_user_id': self.env.user.id,
            'approve_time': datetime.now(),
        })
        if next_line_rec:
            all_user_ids = []
            if next_line_rec.user_ids or next_line_rec.bypass_user_ids:
                view = self.env.ref('approval_matrix.user_selection_form_view')
                stage_config_id = False
                if next_line_rec.dam_conf_line_id and \
                        next_line_rec.dam_conf_line_id.stage_config_ids:
                    stage_config_id = \
                        next_line_rec.dam_conf_line_id.stage_config_ids[0]
                all_user_ids = \
                    next_line_rec.user_ids.ids + \
                    next_line_rec.bypass_user_ids.ids
                # check delegation part
                if stage_config_id and stage_config_id.multi_user_all_ids:
                    for multi_user_all_rec in \
                            stage_config_id.multi_user_all_ids:
                        if multi_user_all_rec.active_delegate:
                            if multi_user_all_rec.allowed_user.id in \
                                    all_user_ids:
                                all_user_ids.pop(all_user_ids.index(
                                    multi_user_all_rec.allowed_user.id))
                            if multi_user_all_rec.delegate_user.id not in \
                                    all_user_ids:
                                all_user_ids.append(
                                    multi_user_all_rec.delegate_user.id)
                ctx = dict(self._context)
                ctx.update({'user_ids': list(set(all_user_ids)),
                            'default_conf_history_line_id': next_line_rec.id,
                            'rec_model': rec_model,
                            'rec_id': rec_id})
                return_data = {
                    'name': _('User Selection'),
                    'context': ctx,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'user.selection',
                    'views': [(view.id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }
                # if len(next_line_rec.user_ids.ids) > 1 or len(
                #         next_line_rec.bypass_user_ids) > 1:
                if len(all_user_ids) > 1:
                    return return_data
            next_line_rec.write({
                'state': 'open',
                'assigned_time': datetime.now(),
            })
            next_line_rec.user_ids = [(6, 0, all_user_ids)]
            try:
                current_rec = self.env[rec_model].browse(rec_id)
                if current_rec:
                    current_rec.state = next_line_rec.name
                    if stage_config_id:
                        if stage_config_id.action_id:
                            self._execute_server_action(
                                stage_config_id.action_id, rec_model, rec_id)
                    return {}
            except:
                return {}

    @api.model
    def check_attachment_validation(self, stage_config_rec, model_name,
                                    rec_id):
        if stage_config_rec.attachment_mandatory:
            attachment_rec = self.env['ir.attachment'].search(
                [('res_id', '=', rec_id), ('res_model', '=', model_name)])
            if len(attachment_rec) < 1:
                raise Warning(_('You cannot change stage without attach a '
                                'document. Please, save the Record then '
                                'attach a document.'))
            return True

    @api.model
    def check_stage_conf_validation(self, conf_line_id, rec_model, rec_id):
        """
        check stage level configuration.
        :param conf_line_id: configuration line id.
        :return:
        """
        conf_line_rec = self.env['dam.conf.line'].browse(conf_line_id)
        if conf_line_rec.stage_config_ids:
            stage_config_rec = conf_line_rec.stage_config_ids[0]
            self.check_attachment_validation(stage_config_rec, rec_model,
                                             rec_id)

    @api.model
    def get_reject_state(self, rec_model):
        """
        :return:
        """
        model = self.env['ir.model'].search([('model', '=', rec_model)])
        if model:
            conf_rec = self.env['dam.conf'].search([('object', '=',
                                                     model.id)], limit=1)
            if conf_rec:
                for conf_line_rec in conf_rec.conf_line_ids:
                    if conf_line_rec.stage_config_ids:
                        stage_config_id = conf_line_rec.stage_config_ids[0]
                        if stage_config_id.is_reject:
                            return conf_line_rec.name.levels
        return False

    @api.model
    def action_reject_record(self, rec_model, rec_id, line_rec, history_rec):
        """
        Reject Record
        :return:
        """
        reject_stage = self.get_reject_state(rec_model)
        if not reject_stage:
            raise Warning(_('Reject Stage not define.'))
        line_rec.write({
            'state': 'open',
            'approve_by_user_id': self.env.user.id,
            'approve_time': datetime.now(),
            'rejected': True
        })
        try:
            current_rec = self.env[rec_model].browse(rec_id)
            if current_rec:
                current_rec.state = reject_stage
        except:
            pass

    @api.model
    def check_all_validation(self):
        """
        :return:
        """
        rec_model = self._context.get('rec_model')
        rec_id = self._context.get('rec_id')
        if rec_model and rec_id:
            history_rec = self.get_history_record(self._context.get(
                'rec_model'), rec_id)
            if history_rec:
                in_progress_state = self.env['dam.conf.history.line'].search([
                    ('dam_conf_id', '=', history_rec.id),
                    ('state', '=', 'open')], order='seq')
                if in_progress_state:
                    # check user allowed to update current document's
                    self.check_user_allocation(in_progress_state)
                    if self._context.get('reject'):
                        self.action_reject_record(rec_model, rec_id,
                                                  in_progress_state,
                                                  history_rec)
                        return {}
                    if self._context.get('btn_rec_id'):
                        # check stage configuration validation.
                        self.check_stage_conf_validation(
                            self._context.get('btn_rec_id'), rec_model, rec_id)
                    return_data = self.update_current_record(rec_model, rec_id,
                                                             in_progress_state,
                                                             history_rec)
                    return return_data
                current_state = self._context.get('c_state', False)
                if current_state:
                    progress_line = self.env['dam.conf.history.line'].search([
                        ('dam_conf_id', '=', history_rec.id),
                        ('name', '=', current_state)], order='seq', limit=1)
                    if progress_line:
                        progress_line.write({'state': 'open',
                                             'assigned_time': datetime.now()})
                        self.check_user_allocation(progress_line)
                        if self._context.get('reject'):
                            self.action_reject_record(rec_model, rec_id,
                                                      progress_line,
                                                      history_rec)
                            return {}
                        if self._context.get('btn_rec_id'):
                            # check stage configuration validation.
                            self.check_stage_conf_validation(
                                self._context.get('btn_rec_id'), rec_model,
                                rec_id)
                            return_data = self.update_current_record(
                                rec_model, rec_id, progress_line, history_rec)
                        return return_data
                else:
                    line_rec = self.env['dam.conf.history.line'].search([
                        ('dam_conf_id', '=', history_rec.id)], order='seq',
                        limit=1)
                    if line_rec:
                        line_rec.write({'state': 'open',
                                        'assigned_time': datetime.now()})
                        self.check_user_allocation(line_rec)
                        if self._context.get('reject'):
                            self.action_reject_record(rec_model, rec_id,
                                                      line_rec, history_rec)
                            return {}
                        if self._context.get('btn_rec_id'):
                            # check stage configuration validation.
                            self.check_stage_conf_validation(
                                self._context.get('btn_rec_id'), rec_model,
                                rec_id)
                            return_data = self.update_current_record(
                                rec_model, rec_id, line_rec, history_rec)
                        return return_data

    name = fields.Char('Name', required="1")
    object = fields.Many2one('ir.model', 'Object')
    conf_line_ids = fields.One2many('dam.conf.line', 'dam_conf_id',
                                    'Conf Line')
    xml_view_id = fields.Many2one('ir.ui.view')
    btn_data = fields.Text()


class DamConfLine(models.Model):
    _name = 'dam.conf.line'
    _order = 'sequence'

    sequence = fields.Integer('Sequence')
    dam_conf_id = fields.Many2one('dam.conf', 'Conf Id')
    name = fields.Many2one('dam.levels', 'Levels')
    default_state = fields.Boolean('Start Flow')
    end_state = fields.Boolean('End Flow')
    stage_config_ids = fields.One2many('stage.config', 'dam_conf_line_id',
                                       'Stage Config')

    def action_view_stage_conf(self):
        """
        add other stage validation like..
        - change Button name
        :return:
        """
        action = self.env.ref('approval_matrix.stage_config_action')
        result = action.read()[0]
        if self.stage_config_ids:
            result['domain'] = "[('id', 'in', " + \
                               str(self.stage_config_ids.ids) + ")]"
            result['res_id'] = self.stage_config_ids[0].id
        else:
            result['context'] = {'default_dam_conf_line_id': self.id,
                                 'default_dam_conf_id': self.dam_conf_id.id,
                                 'default_object': self.dam_conf_id.object.id}
        res = self.env.ref('approval_matrix.stage_config_from', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['create'] = False
        return result
