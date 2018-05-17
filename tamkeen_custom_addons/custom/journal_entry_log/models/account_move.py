from odoo import models, api, fields, tools, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    log_ids = fields.One2many('account.move.log', 'move_id', 'Logs')

    @api.multi
    def review_entry(self):
        for rec in self:
            rec.log_ids.review_log()
        return True

    @api.multi
    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        move_log_obj = self.env['account.move.log']
        for rec in self:
            log_text = "OLD VALUES : \n"
            log_text += "Status:posted"
            log_text += "\nNEW VALUES : \n"
            log_text += "Status:draft"
            move_log_obj.create({
                'move_id': rec.id,
                'move_log': log_text
            })
        return res

    @api.model
    def create(self, vals):
        move_log_obj = self.env['account.move.log']
        if vals is None:
            vals = {}
        old_val_dict = {}
        res = super(AccountMove, self).create(vals)
        keys = vals.keys()
        log_text = ''
        for key in keys:
            if key not in ('line_ids'):
                field_data = res.fields_get().get(key, {})
                value_text = getattr(res, key)
                if field_data.get('relation'):
                    value_text = value_text and value_text.name_get()[0][1] or ''
                old_val_dict.update({
                    field_data.get('string', key): value_text
                })
            log_text = "Journal Item created with values: \n"
        for key, value in old_val_dict.iteritems():
            log_text += tools.ustr(key) + ":" + tools.ustr(value) + "\n"
        if log_text:
            move_log_obj.create({
                'move_id': res.id,
                'move_log': log_text
            })
        return res

    @api.multi
    def write(self, vals):
        move_log_obj = self.env['account.move.log']
        if vals is None:
            vals = {}
        old_val_dict = {}
        new_val_dict = {}
        for rec in self:
            keys = vals.keys()
            for key in keys:
                if key not in ('line_ids'):
                    field_data = rec.fields_get().get(key, {})
                    value_text = getattr(rec, key)
                    if field_data.get('relation'):
                        value_text = value_text and value_text.name_get()[0][1] or ''
                    old_val_dict.update({
                        field_data.get('string', key): value_text
                    })
        res = super(AccountMove, self).write(vals)
        for rec in self:
            log_text = ''
            keys = vals.keys()
            for key in keys:
                if key not in ('line_ids'):
                    field_data = rec.fields_get().get(key, {})
                    value_text = getattr(rec, key)
                    if field_data.get('relation'):
                        value_text = value_text and value_text.name_get()[0][1] or ''
                    new_val_dict.update({
                        field_data.get('string', key): value_text
                    })
            if old_val_dict:
                log_text += "OLD VALUES : \n"
                for key, value in old_val_dict.iteritems():
                    log_text += tools.ustr(key) + ":" + tools.ustr(value) + "\n"
            if new_val_dict:
                log_text += "NEW VALUES : \n"
                for key, value in new_val_dict.iteritems():
                    log_text += tools.ustr(key) + ":" + tools.ustr(value) + "\n"
            if log_text:
                move_log_obj.create({
                    'move_id': rec.id,
                    'move_log': log_text
                })
        return res


class AccountMoveLog(models.Model):
    _name = 'account.move.log'
    _rec_name = 'move_id'
    _order = 'create_date DESC'

    move_id = fields.Many2one('account.move', 'Journal Entry', ondelete="cascade")
    move_log = fields.Text('Modification/Change')
    state = fields.Selection([('draft', 'Draft'), ('reviewed', 'Reviewed')], 'State', default='draft')

    @api.multi
    def review_log(self):
        return self.write({'state': 'reviewed'})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        move_log_obj = self.env['account.move.log']
        if vals is None:
            vals = {}
        old_val_dict = {}
        res = super(AccountMoveLine, self).create(vals)
        keys = vals.keys()
        log_text = ''
        for key in keys:
            if key not in ('line_ids'):
                field_data = res.fields_get().get(key, {})
                value_text = getattr(res, key)
                if field_data.get('relation'):
                    value_text = value_text and value_text.name_get()[0][1] or ''
                old_val_dict.update({
                    field_data.get('string', key): value_text
                })
            log_text = "Journal Entry created with values: \n"
        for key, value in old_val_dict.iteritems():
            log_text += tools.ustr(key) + ":" + tools.ustr(value) + "\n"
        if log_text:
            move_log_obj.create({
                'move_id': res.move_id.id,
                'move_log': log_text
            })
        return res

    @api.multi
    def write(self, vals):
        move_log_obj = self.env['account.move.log']
        if vals is None:
            vals = {}
        old_val_dict = {}
        new_val_dict = {}
        for rec in self:
            keys = vals.keys()
            for key in keys:
                field_data = rec.fields_get().get(key, {})
                value_text = getattr(rec, key)
                if field_data.get('relation'):
                    value_text = value_text and value_text.name_get()[0][1] or ''
                old_val_dict.update({
                    field_data.get('string', key): value_text
                })
        res = super(AccountMoveLine, self).write(vals)
        for rec in self:
            log_text = ''
            keys = vals.keys()
            for key in keys:
                field_data = rec.fields_get().get(key, {})
                value_text = getattr(rec, key)
                if field_data.get('relation'):
                    value_text = value_text and value_text.name_get()[0][1] or ''
                new_val_dict.update({
                    field_data.get('string', key): value_text
                })
            if old_val_dict:
                log_text += "OLD VALUES : \n"
                for key, value in old_val_dict.iteritems():
                    log_text += tools.ustr(key) + ":" + tools.ustr(value) + "\n"
            if new_val_dict:
                log_text += "NEW VALUES : \n"
                for key, value in new_val_dict.iteritems():
                    log_text += tools.ustr(key) + ":" + tools.ustr(value) + "\n"
            if log_text:
                move_log_obj.create({
                    'move_id': rec.move_id.id,
                    'move_log': log_text
                })
        return res
