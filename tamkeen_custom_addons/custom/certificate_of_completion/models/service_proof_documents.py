from odoo import fields, models, api, _


class ServiceProofDocuments(models.Model):
    _inherit = 'service.proof.documents'

    @api.model
    def default_get(self, fields_list):
        res = super(ServiceProofDocuments, self).default_get(fields_list)
        if self._context and self._context.get('certificate_of_completion'):
            model_loan_rec = self.env['ir.model'].search([
                ('model', '=', 'certificate.of.completion')], limit=1)
            res.update({'model_id': model_loan_rec.id})
        return res


class CertificateOfCompletionProof(models.Model):
    _name = 'certificate.of.completion.proof'

    name = fields.Char(string='Name')
    description = fields.Text('Description')
    mandatory = fields.Boolean('Mandatory')
    document = fields.Binary('Document')
    document_file_name = fields.Char('File Name')
    certificate_of_completion_id = fields.Many2one('certificate.of.completion',
                                                   string='Loan Request')