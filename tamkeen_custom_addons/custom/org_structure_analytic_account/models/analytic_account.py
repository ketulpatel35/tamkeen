from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'


    holder_position_id = fields.Many2one('hr.job', string='Holder Position')
    analytic_account_owner_id = fields.Many2one('hr.employee',
                                                string='Analytic Account '
                                                       'Owner',
                                                related='holder_position_id.employee_id', store=True)
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    type = fields.Selection([
        ('view', 'Analytic View/BU'), ('normal', 'Analytic Account'),
        ('contract', 'Contract or Project')], string='Type of Account',
        required=True, default='normal',
        help="If you select the View Type, it means you won\'t allow to create"
             " journal entries using that account.\n The type 'Analytic "
             "account' stands for usual accounts that you only want to use "
             "in accounting.\n If you select Contract or Project, it offers "
             "you the possibility to manage the validity and the invoicing "
             "options for this account.\n The special type 'Template of "
             "Contract' allows you to define a template with default data "
             "that you can reuse easily.")
    parent_id = fields.Many2one(
        'account.analytic.account',
        string='Parent Analytic Account'
    )
    child_ids = fields.One2many('account.analytic.account', 'parent_id',
                                'Child Accounts', copy=True)

    @api.multi
    @api.constrains('parent_id')
    def check_recursion(self):
        for account in self:
            if not super(AccountAnalyticAccount, account)._check_recursion():
                raise UserError(
                    _('You can not create recursive analytic accounts.'),
                )


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    default_analytic_account_id = fields.Many2one('account.analytic.account',
                                                 string='Master Analytic '
                                                        'Account')
    other_analytic_account_ids = fields.Many2many(
        'account.analytic.account', 'account_analytic_department_rel',
        'other_analytic_account_id', 'department_id', string='Other Analytic Accounts')

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        super(HrDepartment, self).onchange_parent_id()
        if self.parent_id:
            self.default_analytic_account_id = \
                self.parent_id.default_analytic_account_id


class HrJob(models.Model):
    _inherit = 'hr.job'

    analytic_account_id = fields.Many2one('account.analytic.account',
                                                  string='Analytic Account')

    @api.onchange('department_id')
    def onchange_department_id(self):
        super(HrJob, self).onchange_department_id()
        if self.department_id:
            self.analytic_account_id = \
                self.department_id.default_analytic_account_id

