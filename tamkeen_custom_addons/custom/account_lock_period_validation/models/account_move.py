from odoo import models, api, fields, tools, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def _is_admin(self):
        res = super(ResUsers, self)._is_admin()
        if not res and self.has_group('journal_entry_log.group_lock_transaction_finance'):
            return True
        return res


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    @api.multi
    def execute_custom(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _validate_fiscalyear_lock(self, values):
        if values.get('fiscalyear_lock_date'):
            nb_draft_entries = self.env['account.move'].search([
                ('company_id', 'in', [c.id for c in self]),
                ('state', '=', 'draft'),
                ('date', '<=', values['fiscalyear_lock_date'])])
            if nb_draft_entries:
                raise ValidationError(_('There are still unposted entries in the period you want to lock. You should either post or delete them.'))

    @api.multi
    def write(self, values):
        if values is None:
            values = {}
        self._validate_fiscalyear_lock(values)
        if values.get('fiscalyear_lock_date', False):
            data_pool = self.env['ir.model.data']
            template_pool = self.env['mail.template']
            old_date = False
            for rec in self:
                old_date = rec.fiscalyear_lock_date
            new_date = values['fiscalyear_lock_date']
            template_id = data_pool.get_object_reference('account_lock_period_validation', 'email_template_locking_date_change')
            if template_id and template_id[1]:
                template_rec = template_pool.browse(template_id[1])
                if not template_rec.email_to:
                    raise ValidationError(_('Kindly configure "Email To" for Locking Date Change email template!'))
                email_body = """
Dear Team,<br/>
This is to notify, the Lock date of Journal Entry is changed from %s to %s.<br/>
This will enable to modify all entries after %s.<br/>
Thanks,
                """ % (old_date, new_date, new_date)
                template_rec.write({'body_html': email_body})
                template_rec.send_mail(rec.id, force_send=True)
        return super(ResCompany, self).write(values)
