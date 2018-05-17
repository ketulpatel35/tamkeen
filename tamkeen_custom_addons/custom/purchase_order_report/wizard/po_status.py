from odoo import models, fields, api, _
from openerp.exceptions import UserError


class PO_Status_Report(models.TransientModel):
    _name = 'purchase.order.status.report'

    partner_id = fields.Many2one('res.partner', string="Vendor")
    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)

    @api.multi
    def get_po_status_detail(self):

        if self.partner_id:
            res = self.env['purchase.order'].\
                search([('partner_id', '=', self.partner_id.id),
                        ('date_approve', '>=', self.date_from),
                        ('state', 'not in', ['draft', 'sent'])])
        else:
            res = self.env['purchase.order'].\
                search([('date_approve', '>=', self.date_from),
                        ('state', 'not in', ['draft', 'sent'])])

        record = []
        if res:
            for rec in res:
                if self.date_to and rec.date_order <= self.date_to:
                    record.append(rec.id)
                else:
                    record.append(rec.id)
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'purchase_order_report.po_status_template',
                'datas': {'ids': record},
            }
        else:
            raise UserError(_('No Records Found For this Criteria'))
