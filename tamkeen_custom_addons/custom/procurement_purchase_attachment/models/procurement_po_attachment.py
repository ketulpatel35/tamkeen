from odoo import models, api


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        '''
        Create Method for find the Products Attachment and Add in PO
        :param vals:Dictionary
        :return: Singelton
        '''
        res = super(PurchaseOrder, self).create(vals)
        pr_obj = self.env['purchase.requisition']
        attach_obj = self.env['ir.attachment']
        if self._context and self._context.get('active_id') and \
                self._context.get(
                'active_model') == 'purchase.requisition':
            pr_rec = pr_obj.browse(self._context.get('active_id'))
            attachment_rec = attach_obj.search([
                ('res_model', '=', pr_rec._name), ('res_id', '=', pr_rec.id)])
            for attachment in attachment_rec:
                attachment_data = {
                    'name': attachment.name,
                    'datas_fname': 'Sample',
                    'datas': attachment.datas,
                    'res_model': 'purchase.order',
                    'res_id': res.id,
                }
                attachment_rec = attach_obj.search([
                    ('name', '=', attachment.name), ('res_id', '=', res.id)])
                if not attachment_rec:
                    attach_obj.create(attachment_data)
        return res
