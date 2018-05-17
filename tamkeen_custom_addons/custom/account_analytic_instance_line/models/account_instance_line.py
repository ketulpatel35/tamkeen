from odoo import models, fields, api


class AccountInstanceLine(models.Model):
    _name = 'account.instance.line'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    @api.multi
    def name_get(self):
        """
        name should display with code
        :return:
        """
        res = []
        for record in self:
            code = record.code or ''
            name = record.name or ''
            display_name = code + '[ ' + name + ' ]'
            res.append((record.id, display_name.title()))
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice.line'

    account_analytic_line_id = \
        fields.Many2one('account.instance.line', string='Analytic Distibution')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    account_analytic_line_id = \
        fields.Many2one('account.instance.line', string='Analytic Distibution')

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMoveLine, self).default_get(fields_list)
        if self._context:
            if self._context.get('date_maturity'):
                res.update({'date_maturity': self._context.get(
                    'date_maturity')})
        return res


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    account_analytic_line_id = \
        fields.Many2one('account.instance.line', string='Analytic Distibution')
