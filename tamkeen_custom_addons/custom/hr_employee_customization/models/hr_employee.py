from odoo import models, api, fields, _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.exceptions import Warning
from openerp.exceptions import UserError
from days360 import get_date_diff_days360

#
# class HrChildren(models.Model):
#     _name = 'hr.employee.children'
#     _description = 'HR Employee Children'
#
#     name = fields.Char(string='Name')
#     dob = fields.Date(string='Date of Birth')
#     employee_id = fields.Many2one('hr.employee', string='Employee')

#
class hr_emergency_contact(models.Model):
    _name = 'hr.emergency.contact'

    name = fields.Char(string='Name')
    mobile_number = fields.Char(string='Mobile Number')
    email_address = fields.Char(string='Email')
    employee_id = fields.Many2one('hr.employee', string='Employee')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.onchange('address_id')
    def _onchange_address(self):
        return False

    def _get_contracts_list(self, employee):
        '''Return list of contracts in chronological order'''
        contracts = []
        for c in employee.contract_ids:
            l = len(contracts)
            if l == 0:
                contracts.append(c)
            else:
                dCStart = datetime.strptime(c.date_start, OE_DATEFORMAT).date()
                i = l - 1
                while i >= 0:
                    dContractStart = datetime.strptime(
                        contracts[i].date_start, OE_DATEFORMAT).date()
                    if dContractStart < dCStart:
                        contracts = contracts[:i + 1] + [c] + contracts[i + 1:]
                        break
                    elif i == 0:
                        contracts = [c] + contracts
                    i -= 1
        return contracts

    def _get_days_in_month(self, d):
        last_date = d - timedelta(days=(d.day - 1)) + relativedelta(
            months=+1) + relativedelta(days=-1)
        return last_date.day

    @api.multi
    def get_months_service_to_date(self):
        '''Returns a dictionary of floats. The key is the employee id, and the
        value is
        number of months of employment.'''

        res = dict.fromkeys(self._ids, 0)
        dToday = date.today()

        for ee in self:
            delta = relativedelta(dToday, dToday)
            contracts = self._get_contracts_list(ee)
            if len(contracts) == 0:
                res[ee.id] = (0.0, False)
                continue

            dInitial = datetime.strptime(
                contracts[0].date_start, OE_DATEFORMAT).date()

            if ee.initial_employment_date:
                dFirstContract = dInitial
                dInitial = datetime \
                    .strptime(ee.initial_employment_date, OE_DATEFORMAT).date()
                delta = relativedelta(dFirstContract, dInitial)

            for c in contracts:
                dStart = datetime.strptime(c.date_start, OE_DATEFORMAT).date()
                if dStart >= dToday:
                    continue

                # If the contract doesn't have an end date, use today's date
                # If the contract has finished consider the entire duration of
                # the contract, otherwise consider only the months in the
                # contract until today.
                #
                if c.date_end:
                    dEnd = datetime.strptime(c.date_end, OE_DATEFORMAT).date()
                else:
                    dEnd = dToday
                if dEnd > dToday:
                    dEnd = dToday

                delta += relativedelta(dEnd, dStart)

            # Set the number of months the employee has worked
            date_part = float(delta.days) / float(
                self._get_days_in_month(dInitial))
            res[ee.id] = (
                float((delta.years * 12) + delta.months) + date_part, dInitial)
        return res

    @api.multi
    def _get_employed_months(self):
        for rec in self:
            _res = rec.get_months_service_to_date()
            for k, v in _res.iteritems():
                rec.length_of_service = v[0]

    @api.multi
    def _get_employed_days(self):
        for rec in self:
            date_diff = 0.0
            if rec.initial_employment_date:
                start_date = \
                    datetime.strptime(rec.initial_employment_date,
                                      OE_DATEFORMAT).date()
                date_diff = \
                    get_date_diff_days360(start_date, date.today())
            rec.length_of_service_days = date_diff

    internal_number = fields \
        .Char(string='Internal Number', help='Internal phone number.')
    short_number = fields \
        .Char(string='Short Number', help='Short phone number.')
    initial_employment_date = fields.Date(
        'Hiring Date',
        help='Date of first employment if it was before'
        ' the start of the first contract'
        ' in the system.')
    length_of_service_days = fields \
        .Integer(compute='_get_employed_days', string='Lenght of Service by '
                                                      'Days', help='Number '
                                                                   'of '
                                                                   'employee service days based on 360 a year.')
    length_of_service = fields \
        .Float(compute='_get_employed_months', string='Lenght of Service')
    fam_spouse = fields.Char(string="Name")
    fam_spouse_employer = fields.Char(string="Employer")
    fam_spouse_tel = fields.Char(string="Phone.")
    # fam_children_ids = fields \
    #     .One2many('hr.employee.children', 'employee_id', string='Children')
    fam_father = fields.Char(string="Name")
    fam_father_dob = fields.Date(string='Date of Birth')
    fam_mother = fields.Char(string="Name")
    fam_mother_dob = fields \
        .Date(string='Date of Birth')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ])
    emergency_contact_ids = fields.\
        One2many('hr.emergency.contact',
                 'employee_id',
                 string='Emergency Contacts')

    # _sql_constraints = [
    #     ('unique_identification_id', 'unique(identification_id)',
    #      _('Official Identifications must be unique!')),
    # ]
    @api.multi
    def _check_unique_country_and_number(self, country_rec,
                                         number):
        if country_rec.code == 'SA':
            result = self.search([('country_id', '=', country_rec.id),
                                  ('identification_id', '=', number)])
            if result:
                return True
            else:
                return False
        else:
            result = self.search([('country_id', '=', country_rec.id),
                                  ('iqama_number', '=', number)])
            if result:
                return True
            else:
                return False

    @api.model
    def create(self, vals):
        if vals.get('country_id'):
            country_rec = self.env['res.country'].browse(
                vals.get('country_id'))
            if country_rec.code == 'SA':
                if vals.get('identification_id'):
                    record = self._check_unique_country_and_number(
                        country_rec, vals.get('identification_id'))
                    if record:
                        raise Warning('Identification number for this country '
                                      'is '
                                      'allready exist')
            else:
                if vals.get('iqama_number'):
                    record = self._check_unique_country_and_number(
                        country_rec, vals.get('iqama_number'))
                    if record:
                        raise Warning('Iqama number for this country is '
                                      'allready exist')
        res = super(HrEmployee, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('country_id') or vals.get('identification_id') or \
                vals.get('iqama_number'):
            if vals.get('country_id'):
                country_rec = self.env['res.country'].browse(
                    vals.get('country_id'))
            else:
                country_rec = self.country_id

            if vals.get('identification_id'):
                record = self._check_unique_country_and_number(
                    country_rec, vals.get('identification_id'))
                if record:
                    raise Warning(
                        'Identification number for this Nationality(Country) '
                        'is allready exist')
            if vals.get('iqama_number'):
                record = self._check_unique_country_and_number(
                    country_rec, vals.get('iqama_number'))
                if record:
                    raise Warning(
                        'Iqama number for this Nationality(Country) is '
                        'allready exist')

        res = super(HrEmployee, self).write(vals)
        return res

    @api.onchange('user_id')
    def _onchange_user(self):
        return False

    @api.multi
    def unlink(self):
        if self.status != 'new':
            raise UserError(_('You cannot Delete Employee who are in not in '
                              '"New Hire State"'))
        return super(HrEmployee, self).unlink()
