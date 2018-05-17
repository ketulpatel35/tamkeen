from odoo import models, api, fields
from dateutil.relativedelta import relativedelta


class EmployeeFamilyInfo(models.Model):
    _name = 'employee.family.info'

    @api.model
    def _age_calculate(self):
        """
        calculate age
        :return:
        """
        for record in self:
            if record.birth_date:
                return relativedelta(
                    fields.Date.from_string(fields.Date.today()),
                    fields.Date.from_string(record.birth_date)).years
            else:
                return 0

    @api.multi
    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            age = record._age_calculate()
            record.age = age

    def _search_age(self, operator, value):
        rec_list = []
        if operator in ('<', '>', '=', '!=', '<=', '>=') and value:
            for rec in self.env['employee.family.info'].search([]):
                age = rec._age_calculate()
                if operator == '<':
                    if age < value:
                        rec_list.append(rec.id)
                elif operator == '>':
                    if age > value:
                        rec_list.append(rec.id)
                elif operator == '=':
                    if age == value:
                        rec_list.append(rec.id)
                elif operator == '!=':
                    if age != value:
                        rec_list.append(rec.id)
                elif operator == '<=':
                    if age <= value:
                        rec_list.append(rec.id)
                elif operator == '>=':
                    if age >= value:
                        rec_list.append(rec.id)
        return [('id', 'in', rec_list)]

    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee ID')
    name = fields.Char(string='Name')
    arabic_name = fields.Char(string='Arabic Name')
    # job_name = fields.Char(string='Job Name')
    emergency_contact = fields.Boolean(string='Emergency Contact')
    mobile_number = fields.Char(string='Mobile Number')
    relationship = fields.Selection([('father', 'Father'), ('mother',
                                                            'Mother'),
                                     ('husband', 'Husband'), ('wife', 'Wife'),
                                     ('daughter', 'Daughter'), ('son',
                                                                'Son'),
                                     ('others', 'Others')],
                                    string='Relationship')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              'Gender')
    marital_status = fields.Selection(
        [('single', 'Single'), ('married', 'Married'),
         ('widower', 'Widower'),
         ('divorced', 'Divorced')],
        'Marital Status')
    birth_date = fields.Date(string='Birth Date')
    age = fields.Integer(string='Age', readonly=True,
                         compute='_compute_age', search='_search_age')
    country_id = fields.Many2one('res.country', 'Nationality')
    id_type = fields.Selection([('national_id', 'National ID'),
                                ('iqama_number', 'Iqama Number'),
                                ('boarding_number', 'Boarding Number')],
                               string='ID Type')
    id_iqama = fields.Char(string='ID/Iqama Number')
    passport_no = fields.Char(string='Passport')
    passport_expiry_date = fields.Date(string='Passport Expiry Date')
    inside_ksa = fields.Boolean(string='Inside KSA')
    insurance_covered = fields.Boolean(string='Insurance Covered')
    remarks = fields.Text(string='Remarks')
