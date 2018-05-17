from odoo import api, fields, models, _
from odoo.exceptions import Warning

class HrContract(models.Model):
    _inherit = 'hr.contract'

    # @api.onchange('grade_level')
    # def onchange_grade_level(self):
    #     if self.grade_level:
    #         self.wage = self.grade_level.wage

    grade_level = fields.Many2one('grade.level', string='Grade Level')
    # field alredy in hr_contract_state module
    # wage = fields.Float(string='Wage', required=True, store=True,
    #                    help="Basic Salary of the employee"),

    # @api.model
    # def create(self, vals):
    #     grade_level_id = vals.get('grade_level', False)
    #     if grade_level_id:
    #         grade_level_rec = self.env['grade.level'].browse(grade_level_id)
    #         vals['wage'] = grade_level_rec.wage
    #     return super(HrContract, self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     grade_level_id = vals.get('grade_level', False)
    #     if grade_level_id:
    #         grade_level_rec = self.env['grade.level'].browse(
    #             grade_level_id)
    #         vals['wage'] = grade_level_rec.wage
    #     return super(HrContract, self).write(vals)


class grade_level(models.Model):
    _name = 'grade.level'
    _description = 'Grade Level'
    _order = 'name'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        args = args or []
        records = self.search([('name', operator, name)] + args, limit=limit)
        return records.name_get()

    name = fields.Char('Grade', help='The salary structure grade.')
    minimum_value = fields.Float(string='Minimum Value')
    maximum_value = fields.Float(string='Maximum Value')
    wage = fields.Float('Common Wage', help="Common Basic Salary for this "
                                            "grade")
    holidays_status_ids = fields.\
        Many2many('hr.holidays.status',
                  'hr_holidays_status_grade_rel',
                  'grade_id',
                  'holiday_status_id',
                  string='Leave Types')
    code = fields.Char(string='Code')
    maximum_allowed_annual_balance = fields.Float(string='Maximum Allowed '
                                                         'Annual Balance')
    maximum_accumulative_balance = fields.Float(
        string='Maximum Accumulative Balance')
    trial_period = fields.Float(
        string='Trial Period(Days)')
    active = fields.Boolean(string='Active', default=True)

    def _check_warning(self):
        raise Warning(_('The common wage should be within the '
                        'minimum and maximum values.'))

    @api.model
    def create(self, vals):
        if vals.get('minimum_value') and vals.get('maximum_value') and \
                vals.get('wage'):
            if vals.get('wage') < vals.get('minimum_value') or vals.get(
                    'wage') > vals.get('maximum_value'):
                self._check_warning()
        return super(grade_level, self).create(vals)

    @api.multi
    def write(self, vals):
        for rec in self:
            minimum_value = vals.get('minimum_value') if vals.get(
                'minimum_value') else rec.minimum_value
            maximum_value = vals.get('maximum_value') if vals.get(
                'maximum_value') else rec.maximum_value
            wage = vals.get('wage') if vals.get('wage') else rec.wage
            if wage < minimum_value or wage > maximum_value:
                rec._check_warning()
        return super(grade_level, self).write(vals)