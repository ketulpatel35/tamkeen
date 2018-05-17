from odoo import models, api, fields


class ReviewJournalLog(models.TransientModel):
    _name = 'review.journal.log'

    @api.multi
    def review_log(self):
        context = dict(self._context) or {}
        if context.get('active_ids', []):
            self.env['account.move.log'].browse(context['active_ids']).review_log()
        return True
