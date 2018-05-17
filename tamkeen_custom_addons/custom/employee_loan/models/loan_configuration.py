from odoo import fields, models, api, _
from datetime import datetime as dt
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
# class LoanProof(models.Model):
#     _name = 'loan.proof'
#     _description = 'Loan Proofs'
#
#     name = fields.Char('Name')
#     model_id = fields.Many2one('ir.model', string='Add-on')
#     description = fields.Text('Description')
#     active = fields.Boolean('Active', default=True)
#     mandatory = fields.Boolean('Mandatory')
#
#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None, count=False,
#                 access_rights_uid=None):
#         if args is None:
#             args = []
#         if self._context.get('loan_conf_id'):
#             config_rec = self.env['service.configuration.panel'].browse(
#                 self._context.get('loan_conf_id'))
#             args.append(('id', 'in', config_rec.service_proof_ids.ids))
#
#         return super(LoanProof, self)._search(args, offset=offset,
#                                               limit=limit, order=order,
#                                               count=count, access_rights_uid=
#                                               access_rights_uid)


class LoanConfigurationPanel(models.Model):
    _inherit = 'service.configuration.panel'
    _description = 'Loan Configuration Panel'

    @api.depends('model_id')
    def check_loan(self):
        """
        check is loan
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'hr.employee.loan':
                rec.is_loan = True

    is_loan = fields.Boolean('Is Loan Policy', compute='check_loan',
                             store=True)
    service_policy_ids = fields.One2many('loan.policy', 'service_id',
                                         string='Policy')
    loan_installment_policy = fields.Selection([
        ('deserved', 'Deserved'),
        ('desired', 'Desired')], string='Installment Policy',
        default='deserved')
    allow_multiple_active_loans = fields.Boolean(string='Allow employee '
                                                        'to have mutiple '
                                                        'active loans')
    repayment_method = fields.Selection([('payroll', 'Payroll'),
                                         ('cash_bank', 'Cash/Bank')],
                                        string='RePayment Method',
                                        default='payroll')
    maximum_loan_per_calender_year = fields.Integer(string='Maximum Loans '
                                                           'Per Calendar Year')
    employee_loan_rule_input = fields.Many2one('hr.rule.input',
                                                 string='Employee Loan Rule '
                                                        'Input')
    performance_evaluation_required = fields.Boolean(string='Performance '
                                                            'Evaluation '
                                                            'Required')
    employee_performance_evaluation = fields.Float(
        'Employee Performance Evaluation Limit')
    ask_for_reschedule_email = fields.Char('Ask for Reschedule Email to')
    minimum_loan_amount = fields.Integer(string='Minimum Loan Amount to '
                                                'Request')
    clearance_report_valid = fields.Integer(string='Clearance Report '
                                                   'Validate up to',
                                            default=15)
    clearance_report_valid_unit = fields.Selection([('Day/s', 'Day/s'),
                                                    ('Month/s', 'Month/s'),
                                                    ('Year/s', 'Year/s')],
                                                   default='Day/s')
    clearance_report_contact = fields.Char('Clearance Report Contact Email')

    # hr.employee.loan
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('valid_loan'):
            domain = [('model_id.model', '=', 'hr.employee.loan')]
            today_date = dt.today().date()
            records_ids = []
            for rec in self.search(domain):
                if rec.valid_from_date and rec.valid_to_date:
                    from_date = dt.strptime(rec.valid_from_date,
                                            OE_DATEFORMAT).date()
                    to_date = dt.strptime(rec.valid_to_date,
                                          OE_DATEFORMAT).date()
                    if from_date <= today_date <= to_date:
                        records_ids.append(rec.id)
            if records_ids:
                return self.browse(records_ids).name_get()
        return super(LoanConfigurationPanel, self).name_search(
            name, args, operator, limit)

class LoanPolicy(models.Model):
    _name = 'loan.policy'

    # installment_policy = fields.Selection([
    #     ('deserved', 'Deserved'),
    #     ('desired', 'Desired')], string='Installment Policy')
    # allow_multiple_loans = fields.Boolean('Allow Multiple Loan')
    # repayement_method = fields.Selection([
    #     ('payroll', 'Payroll'),
    #     ('cashbank', 'Cash/Bank')], string='RePayment Method')
    # max_loans_per_year = fields.Integer('Max Loans per year')

    name = fields.Char('Name')
    code = fields.Char('Code')
    company_experience_from = fields.Integer('Company Experience From ('
                                             '#Years)')
    company_experience_to = fields.Integer(
        'Company Experience To (#Years)')
    deserved_amount = fields.Float('Deserved Amount Number')
    deserved_amount_salary_rule_id = fields.Many2one('hr.salary.rule',
                                                 string='Deserved Amount '
                                                            'Salary Rule')
    loan_deduction_period = fields.Integer('Loan Deduction Period (Months)')
    notes = fields.Text('Notes')
    service_id = fields.Many2one('service.configuration.panel')


class ServiceProofDocuments(models.Model):
    _inherit = 'service.proof.documents'

    @api.model
    def default_get(self, fields_list):
        res = super(ServiceProofDocuments, self).default_get(fields_list)
        if self._context and self._context.get('is_loan'):
            model_loan_rec = self.env['ir.model'].search([
                ('model', '=', 'hr.employee.loan')], limit=1)
            res.update({'model_id': model_loan_rec.id})
        return res


class LoanProof(models.Model):
    _name = 'loan.proof'

    name = fields.Char(string='Name')
    description = fields.Text('Description')
    mandatory = fields.Boolean('Mandatory')
    document = fields.Binary('Document')
    document_file_name = fields.Char('File Name')
    loan_id = fields.Many2one('hr.employee.loan', string='Loan Request')