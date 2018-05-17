from odoo import fields, models, api
import re


class hr_employee_profile(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    sponsorname = fields.Char(string='Sponsor Name')
    sponsoraddress = fields.Char(string='Sponsor Address')
    sponsorphone = fields.Char(string='Sponsor Phone')
    experiences_line_id = fields.One2many('tamkeen.hr.experiences', 'emp_line',
                                          string='Experiences',
                                          ondelete='cascade')
    qualifications_line_id = fields.One2many('tamkeen.hr.qualifications',
                                             'emp_line',
                                             string='Qualifications',
                                             ondelete='cascade')
    trainings_line_id = fields.One2many('tamkeen.hr.trainings', 'emp_line',
                                        string='Trainings',
                                        ondelete='cascade')

    @api.multi
    def _check_iban_value(self):
        for record in self:
            pattern = "^[0-9A-Z]*[0-9]$"
            if record.bank_account:
                if re.match(pattern, record.bank_account):
                    return True
                else:
                    return False
        return True

    _constraints = [
        (_check_iban_value, 'Employee Bank Account Number Should Be '
                            'Capital Letter And Number Only".',
         ['bank_account']),
    ]
