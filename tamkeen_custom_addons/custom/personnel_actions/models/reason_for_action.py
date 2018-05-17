from odoo import api, models, fields


class ReasonForAction(models.Model):
    _name = 'reason.for.action'
    _description = 'Reason For Action'


    name = fields.Char(string='Name')
    code = fields.Char(strin='Code')
    description = fields.Text(string='Description')
    personnel_action_type_id = fields.Many2one('personnel.action.type',
                                               string='Personnel Action Type')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        args = args or []
        if self._context.get('action_type_id'):
            action_type_rec = self.env['personnel.action.type'].browse(self._context.get(
                'action_type_id'))
            if action_type_rec.reason_action_ids:
                records = self.search(
                    [('id', 'in', action_type_rec.reason_action_ids.ids)],
                    limit=limit)
                return records.name_get()
        return self.name_get()