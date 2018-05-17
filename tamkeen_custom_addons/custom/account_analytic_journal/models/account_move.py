from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.one
    def _prepare_analytic_line(self):
        """ Prepare the values used to create() an account.analytic.line
        upon validation of an account.move.line having an analytic account.
        This method is intended to be extended in other modules.
        - add analytic journal
        """
        res = super(AccountMoveLine, self)._prepare_analytic_line()[0]
        if res and self.journal_id and self.journal_id.analytic_journal_id:
            res.update({
                'journal_id': self.journal_id.analytic_journal_id.id})
        return res
