from odoo import fields, models, api, _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DTFORMAT
from odoo.exceptions import Warning

class BenefitsProgramDependents(models.Model):
    _name = 'benefits.program.dependents'
    _description = 'Benefits Program Dependents'

    @api.depends('school_fee', 'admission_fee')
    def calculate_total_fee(self):
        """
        calculate total fee
        :return:
        """
        for rec in self:
            rec.total_fees = rec.school_fee + rec.admission_fee

    benefits_program_id = fields.Many2one('org.benefits.program',
                                          'Benefits Program')
    child_id = fields.Many2one('employee.family.info', string='Child Name')
    birth_date = fields.Date('Date of Birth')
    age = fields.Integer('Age')
    school_fee = fields.Float('School Fee')
    admission_fee = fields.Float('Admission Fee')
    remarks = fields.Text('Remarks')
    total_fees = fields.Float('Total Fees', compute='calculate_total_fee',
                              store=True)
    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')

    @api.onchange('child_id')
    def onchange_child_id(self):
        """
        onchange child(s)
        :return:
        """
        if self.child_id:
            self.birth_date = self.child_id.birth_date
            self.age = self.child_id.age

    @api.onchange('benefits_program_id')
    def onchange_benefits_program_id(self):
        """
        :return:
        """
        res = {'child_id': []}
        if self.benefits_program_id and self.benefits_program_id.employee_id:
            min_age = self.benefits_program_id.benefits_program_policy_id\
                          .allow_min_age or 0
            max_age = self.benefits_program_id.benefits_program_policy_id\
                          .allow_max_age or 0
            res['child_id'] = [
                ('employee_id', '=', self.benefits_program_id.employee_id.id),
                ('relationship', 'in', ['son', 'daughter']),
                ('age', '>=', min_age), ('age', '<=', max_age)]
        return {'domain': res}

    @api.constrains('date_from', 'date_to')
    def _check_date_validations(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                date_from = datetime.strptime(rec.date_from, DTFORMAT).date()
                date_to = datetime.strptime(rec.date_to, DTFORMAT).date()
                if date_to < date_from:
                    raise Warning(
                        _('The start date must be anterior to the end date.'))


class OrgSubBenefitsProgram(models.Model):
    _name = 'org.sub.benefits.program'
    _description = 'Sub Benefits Program'

    benefits_program_id = fields.Many2one(
        'org.benefits.program', 'Benefits Program')
    name = fields.Many2one('bp.sub.benefits', 'Sub Benefits')
    amount = fields.Float('Amount')
    remarks = fields.Text('Remarks')
    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')

    @api.onchange('benefits_program_id')
    def onchange_benefits_program_id(self):
        """
        :return:
        """
        res = {}
        sub_benefits_ids = []
        if self.benefits_program_id and \
                self.benefits_program_id.benefits_program_policy_id and \
                self.benefits_program_id.is_display_sub_benefits:
            sub_benefits_ids = \
                self.benefits_program_id.benefits_program_policy_id \
                    .bp_sub_benefits_ids.ids
        res.update(
            {'name': [('id', 'in', sub_benefits_ids)]})
        return {'domain': res}

    @api.constrains('date_from', 'date_to')
    def _check_date_validations(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                date_from = datetime.strptime(rec.date_from, DTFORMAT).date()
                date_to = datetime.strptime(rec.date_to, DTFORMAT).date()
                if date_to < date_from:
                    raise Warning(
                        _('The start date must be anterior to the end date.'))