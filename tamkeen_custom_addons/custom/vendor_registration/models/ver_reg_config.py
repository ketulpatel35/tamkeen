from odoo import models, fields


class FinancialStatementConfiguration(models.Model):
    _name = 'financial.statement.configuration'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    _sql_constraints = [('financial_statement_code_unique', 'UNIQUE(code)',
                         "The code must be unique !")]


class DualityHse(models.Model):
    _name = 'quality.hse'

    name = fields.Char(string='Quality & HSE')
    code = fields.Char(string='Code')

    _sql_constraints = [('quality_hse_code_unique', 'UNIQUE(code)',
                         "The code must be unique !")]


class DocumentCertificateAttachment(models.Model):
    _name = 'document.certificate.attachment'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    _sql_constraints = [('document_certificate_code_unique', 'UNIQUE(code)',
                         "The code must be unique !")]


class ProcrumentTemplate(models.Model):
    _name = 'procrument.template'
    _description = 'Procrument Template'
    _rec_name = 'category'

    category = fields.Selection([('general', 'General'), ('others',
                                                          'Others')],
                                default='general')
    survey_template_id = fields.Many2one('survey.survey', string='Template')


class AccountingInformation(models.Model):
    _name = 'accounting.information'
    _description = 'Accounting Information'

    currency_id = fields.Many2one('res.currency', string='Currency')
    name = fields.Char('Bank name')
    bank_branch = fields.Char('Bank branch')
    bank_address = fields.Text('Bank Address')
    account_number = fields.Char('Account Number')
    iban_number = fields.Char('IBAN number')
    swift_code = fields.Char('SWIFT code')
    vendor_reg_id = fields.Many2one('vendor.registration',
                                    string='Vendor Registration')