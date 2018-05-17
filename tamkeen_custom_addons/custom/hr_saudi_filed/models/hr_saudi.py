#!/usr/bin/env python
# -*- coding: utf-8 -*
from odoo import fields, api, models, _
from hijri import Convert_Date
import re
from odoo.exceptions import Warning


# here is the calss hr.holidays.status copy from hy_payroll_period also
# xml code is copoy for the code field so dont repet this code in
# hy_payroll_period
class hr_holidays_status(models.Model):
    _name = 'hr.holidays.status'
    _inherit = 'hr.holidays.status'

    code = fields.Char('Code')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Codes for leave types must be '
                                        'unique!')]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    working_address = fields.Boolean(string='Working Address?')


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _get_annual_leave_balance(self):
        """
        :return:
        """
        for sub_id in self:
            holi_status_obj = self.env['hr.holidays.status']
            holiday_status_id = holi_status_obj.search([('code', '=',
                                                         'ANNLV')])
            if holiday_status_id:
                leaves_bal = holiday_status_id.get_days(self.id)
                sub_id.remaining_leaves = leaves_bal['remaining_leaves']
            else:
                sub_id.remaining_leaves = 0.0

    @api.multi
    def _get_annual_leave_balance(self):
        for sub_id in self:
            sub_id.remaining_leaves = 0

    @api.multi
    def _leaves_count(self):
        Holidays = self.env['hr.holidays']
        for rec in self:
            rec.leaves_count = Holidays.search_count(
                [('employee_id', '=', rec.id), ('type', '=', 'remove'),
                 ('state', '=', 'validate')])

    # HR Settings
    remaining_leaves = fields.Float(compute=_get_annual_leave_balance,
                                    string='Remaining Leaves',
                                    store=True)

    # Citizenship & Other Info
    name_eng = fields.Char(string='Arabic name')
    personal_mobile_number = fields.Char(string='Personal Mobile Number')
    gosi_number = fields.Char(string='GOSI Number')
    iqama_number = fields.Char(string='Iqama Number')
    iqama_exp_date = fields.Date(string='Iqama Expiry Date')
    iqama_exp_date_hijri = fields.Char(string='Iqama Expiry Date Hijri')
    passport_exp_date = fields.Date(string='Passport Expiry Date')
    passport_exp_date_hijri = fields.Char(string='Passport Expiry Date '
                                                 'Hijri')
    job_as_visa = fields.Char(string='Job as Visa')
    accommodation_provided = fields.Boolean('Accommodation Provided')
    insurance_covered = fields.Boolean(string='Insurance Covered')
    insurance_cover_date = fields.Date(string='Date of Cover')
    emp_experience = fields.Selection([('1', '1'), ('2', '2'),
                                       ('3', '3'), ('4', '4'),
                                       ('5', '5'), ('6', '6'),
                                       ('7', '7'), ('8', '8'),
                                       ('9', '9'), ('10', '10'),
                                       ('11', '11'), ('12', '12'),
                                       ('13', '13'), ('14', '14'),
                                       ('15', '15'), ('16', '16'),
                                       ('17', '17'), ('18', '18'),
                                       ('19', '19'), ('20', '20'),
                                       ('21', '21'), ('22', '22'),
                                       ('23', '23'), ('24', '24'),
                                       ('25', '25'), ('26', '26'),
                                       ('27', '27'), ('28', '28'),
                                       ('29', '29'), ('30', '30')
                                       ], string='Employee Experience (Years)')
    religion = fields.Selection([('muslim', 'Muslim'), ('other', 'Other')],
                                string='Religion', default='muslim')

    id_exp_date = fields.Date(string='ID Expiry Date')
    id_exp_date_hijri = fields.Char(string='ID Expiry Date Hijri')
    company_emplyoee_id = fields.Integer(string='Emp ID')
    short_name = fields.Char(string='Short Name', translate=True)

    # Spouse
    # fam_spouse_arabic = fields.Char(string='(Spouse) Arabic Name')
    # spouse_identification_no = fields.Char('(Spouse) Identification No')
    # spouse_passport_id = fields.Char(string='(Spouse) Passport No')
    # spouse_passport_exp_date = fields.Date(
    #     string='(Spouse) Passport Expiry Date')
    # spouse_iqama_number = fields.Char(string='(Spouse) Iqama Number')
    # spouse_iqama_exp_date = fields.Date(string='(Spouse) Iqama Expiry Date')
    # spouse_covered = fields.Boolean(string='(Spouse) Insurance Covered('
    #                                        'Spouse)')
    # spouse_cover_date = fields.Date(string='(Spouse) Date of Cover(Spouse)')
    # Parents
    # Father
    # fam_father_arabic = fields.Char(string='(Father) Arabic Name')
    # fam_father_identification_no = fields.Char('(Father)  Identification No')
    # fam_father_passport_id = fields.Char(string='(Father)  Passport No')
    # fam_father_passport_exp_date = fields.Date(string='(Father)  Passport '
    #                                                   'Expiry Date')
    # fam_father_iqama_number = fields.Char(string='(Father)  Iqama Number')
    # fam_father_iqama_exp_date = fields.Date(string='(Father)  Iqama Expiry '
    #                                                'Date')
    # Mother
    # fam_mother_arabic = fields.Char(string='(Mother) Arabic Name')
    # fam_mother_identification_no = fields.Char('(Mother) Identification No')
    # fam_mother_passport_id = fields.Char(string='(Mother) Passport No')
    # fam_mother_passport_exp_date = fields.Date(string='(Mother) Passport '
    #                                                   'Expiry Date')
    # fam_mother_iqama_number = fields.Char(string='(Mother) Iqama Number')
    # fam_mother_iqama_exp_date = fields.Date(string='(Mother) Iqama Expiry Date')

    bankorcash = fields.Selection((('intrabank', 'Intra Bank Transfer'),
                                   ('thirdparty', 'Third Party Bank'),
                                   ('cash', 'Cash')),
                                  string='Salary Payment')
    bank_id = fields.Many2one('res.bank', string="Bank Name")
    bank_account = fields.Char(string='Employee Bank Account Number')
    bank_locked = fields.Boolean(string='Bank Account Locked')
    bank_locked_start_date = fields.Date(string='Bank Account Locked Start '
                                                'Date')

    leaves_count = fields.Integer(compute=_leaves_count, string='Leaves')
    blood_type = fields.Selection((('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'),
                                   ('b-', 'B-'), ('o+', 'O+'), ('o-', 'O-'),
                                   ('ab+', 'AB+'), ('ab-', 'AB-')),
                                  string='Blood Type')
    birthday_hijri = fields.Char(string='Hijri Date Of Birth')
    current_country_code = fields.Char(related='country_id.code',
                                       string='Saudi Country')
    personal_email = fields.Char(string='Personal Email')
    home_phone_number = fields.Char(string='Home Phone Number')
    address_details = fields.Char('Address Details')
    # address_id: fields.many2one('res.partner', 'Working Address',
    #                             domain="[('is_company','=',True)]"),
    # 'address_home_id': fields.many2one('res.partner', 'Home Address',
    #                                    domain="[('is_company','!=',True)]"),

    # Contact Info
    post_code = fields.Char(string='P.O. Box')
    zip_code = fields.Char(string='Zip Code')

    @api.onchange('personal_email')
    def validate_email(self):
        if self.personal_email:
            if re.match("^[-a-zA-Z0  -9._%+]+@[a-zA-Z0-9._%]+.[a-zA-Z]{2,6}$",
                        self.personal_email) is None:
                raise Warning(_('Invalid Email '
                                'Please enter a valid personal email address'))

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        res = super(hr_employee, self).create(vals)
        if vals.get('personal_email'):
            if re.match("^[-a-zA-Z0  -9._%+]+@[a-zA-Z0-9._%]+.[a-zA-Z]{2,6}$",
                        vals.get('personal_email')) is None:
                raise Warning(_('Invalid Email '
                                'Please enter a valid personal email address'))
        return res

    @api.multi
    def write(self, vals):
        """
        :param vals:
        :return:
        """
        res = super(hr_employee, self).write(vals)
        if vals.get('personal_email'):
            if re.match("^[-a-zA-Z0  -9._%+]+@[a-zA-Z0-9._%]+.[a-zA-Z]{2,6}$",
                        vals.get('personal_email')) is None:
                raise Warning(_('Invalid Email '
                                'Please enter a valid personal email address'))
        return res

    @api.onchange('iqama_exp_date', 'passport_exp_date', 'id_exp_date',
                  'birthday')
    def onchange_issue_date(self):
        self.ensure_one()
        if self._context and self._context.get('english_date'):
            if self.iqama_exp_date:
                self.iqama_exp_date_hijri = Convert_Date(
                    self.iqama_exp_date, 'english', 'islamic')
            if self.passport_exp_date:
                self.passport_exp_date_hijri = Convert_Date(
                    self.passport_exp_date, 'english', 'islamic')
            if self.id_exp_date:
                self.id_exp_date_hijri = Convert_Date(
                    self.id_exp_date, 'english', 'islamic')
            if self.birthday:
                self.birthday_hijri = Convert_Date(
                    self.birthday, 'english', 'islamic')

    @api.onchange('iqama_exp_date_hijri', 'passport_exp_date_hijri',
                  'id_exp_date_hijri', 'birthday_hijri')
    def onchange_hijiri_date(self):
        """
        date convert
        passport_exp_date_hijri
        :return:
        """
        self.ensure_one()
        if self._context and self._context.get('hijri_date'):
            if self.iqama_exp_date_hijri:
                self.iqama_exp_date = Convert_Date(
                    self.iqama_exp_date_hijri, 'islamic', 'english')

            if self.id_exp_date_hijri:
                self.id_exp_date = Convert_Date(
                    self.id_exp_date_hijri, 'islamic', 'english')
            if self.birthday_hijri:
                self.birthday = Convert_Date(
                    self.birthday_hijri, 'islamic', 'english')
            if self.passport_exp_date_hijri:
                self.passport_exp_date = Convert_Date(
                    self.passport_exp_date_hijri, 'islamic', 'english')
