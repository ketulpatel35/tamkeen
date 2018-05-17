# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    note = fields.Text(string='Note')


class hr_payslip_amendment(models.Model):

    _name = 'hr.payslip.amendment'
    _description = 'Pay Slip Amendment'

    _inherit = ['mail.thread']

    @api.model
    def _select_objects(self):
        records = self.env['ir.model'].search([])
        return [(record.model, record.name) for record in records] + [('', '')]

    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code(
            'hr.payslip.amendment') or _('New')
        result = super(hr_payslip_amendment, self).create(vals)
        return result

    code = fields.Char(string='Sequence')
    name = fields.Char(string='Description')
    input_id = fields.Many2one('hr.rule.input', string='Salary Rule Input')
    type = fields.Selection([('addition', 'Addition'),
                             ('deduction', 'Deduction')])
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  track_visibility='onchange')
    amount = fields.\
        Float(string='Amount',
              help="The meaning of this field"
                   " is dependant on the salary rule that uses it.",
              track_visibility='onchange')
    note = fields.Text(string='Remarks')
    employee_company_id = fields.Char(
        related='employee_id.f_employee_no',
        string='Employee Company ID',
        type='char',
        store=True,
        required=False)
    reference_id = fields.Reference(string='Reference',
                                    selection='_select_objects')
    job_id = fields.Many2one('hr.job', 'Position')
    department_id = fields.Many2one(
        'hr.department', string='Organization Unit', copy=False)
    org_unit_type = fields.Selection([
        ('root', 'Root'), ('business', 'Business Unit'),
        ('department', 'Department'), ('section', 'Section')],
        string='Organization Unit Type', copy=False)
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id, string='Company')
    calculation_based_on = fields.Selection([('days_hours', 'Days/Hours'),
                                             ('amount', 'Amount')],
                                            string='Calculation Based on',
                                            default='amount')
    number_of_days = fields.Float(string='Number Of Days',
                                  track_visibility='onchange')
    amendment_hours = fields.Float(string='Hours')
    # corresponding_days_rule = fields.Many2one('hr.payslip.worked_days',
    #                                           string='Corresponding Rule('
    #                                                  'Days)')
    corresponding_rule = fields.Selection([('unpaid', 'Unpaid'),
                                           ('absence', 'Absence')],
                                          string='Corresponding Rule')
    state = fields.Selection((('draft', 'Draft'),
                              ('validate', 'Confirmed'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done'),
                              ), string='State', default='draft',
                             track_visibility='onchange')

    @api.onchange('number_of_days')
    def onchange_number_of_days(self):
        amendment_hours = 0.0
        if self.employee_id and self.employee_id.resource_id and \
                self.employee_id.resource_id.calendar_id and self.employee_id.resource_id.calendar_id.uom_id:
            uom_hour = self.employee_id.resource_id.calendar_id.uom_id or \
                       self.env.ref('product.product_uom_hour',
                                    raise_if_not_found=False)
            uom_day = self.env.ref('product.product_uom_day',
                                   raise_if_not_found=False)
            amendment_hours = uom_day._compute_quantity(
                self.number_of_days, uom_hour) \
                if uom_day and uom_hour \
                else self.number_of_days * 8.0
        self.amendment_hours = amendment_hours

    @api.onchange('amendment_hours')
    def onchange_amendment_hours(self):
        number_of_days = 0
        if self.employee_id and self.employee_id.resource_id and \
                self.employee_id.resource_id.calendar_id and self.employee_id.resource_id.calendar_id.uom_id:
            uom_hour = self.employee_id.resource_id.calendar_id.uom_id or \
                       self.env.ref('product.product_uom_hour',
                                    raise_if_not_found=False)
            uom_day = self.env.ref('product.product_uom_day',
                                   raise_if_not_found=False)
            # if self.amendment_hours:
            number_of_days = uom_hour._compute_quantity(
                self.amendment_hours, uom_day) \
                if uom_day and uom_hour \
                else self.amendment_hours / 8.0
        self.number_of_days = number_of_days

    @api.onchange('calculation_based_on')
    def onchange_calculation_based_on(self):
        self.number_of_days = 0
        self.input_id = False
        self.corresponding_rule = False
        # self.corresponding_days_rule = False
        self.amount = False
        if self.calculation_based_on == 'days_hours':
            self.type = 'deduction'

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            # name = "Pay Slip Amendment: " + self.employee_id.name
            # if self.employee_id.f_employee_no:
            #     name += ' (' + self.employee_id.f_employee_no + ')'
            self.job_id = self.employee_id.job_id and \
                          self.employee_id.job_id or False
            self.department_id = self.employee_id.department_id and \
                                 self.employee_id.department_id.id or False
            self.org_unit_type = self.employee_id.department_id and \
                                 self.employee_id.department_id.org_unit_type
            # self.name = name

    @api.multi
    def unlink(self):
        for psa in self:
            if psa.state in ['validate', 'done']:
                raise UserError(_("Invalid Action"
                                  " A Pay Slip Amendment"
                                  " that has been confirmed"
                                  " cannot be deleted!"))
        return super(hr_payslip_amendment, self).unlink()

    @api.multi
    def do_validate(self):
        for rec in self:
            rec.state = 'validate'

    @api.multi
    def do_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    @api.multi
    def do_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def do_done(self):
        for rec in self:
            rec.state = 'done'
