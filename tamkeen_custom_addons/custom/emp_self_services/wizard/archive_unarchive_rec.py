from odoo import fields, models, api


class ArchiveUnarchiveRecord(models.TransientModel):
    _name = 'emp.archive.unarchive'

    @api.multi
    def action_archive_rec(self):
        """
        :return:
        """
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        if active_model and active_ids:
            for rec in self.env[active_model].browse(active_ids):
                rec.active = False

    @api.multi
    def action_unarchive_rec(self):
        """
        :return:
        """
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        if active_model and active_ids:
            for rec in self.env[active_model].browse(active_ids):
                rec.active = True