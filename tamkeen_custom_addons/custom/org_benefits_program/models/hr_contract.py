from odoo import fields, models, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    entitled_manual_benefits = fields.Boolean('Entitled Manual Benefits')
    education_benefit = fields.Float('Education Benefit')
    flexible_benefit = fields.Float('Flexible Benefit')
    wellness_program = fields.Float('Wellness Program')

    @api.onchange('education_benefit')
    def onchange_education_benefit(self):
        """
        onchange education benefit
        :return:
        """
        if self.education_benefit:
            self.flexible_benefit = 0

    @api.onchange('flexible_benefit')
    def onchange_flexible_benefit(self):
        """
        onchange flexible benefit
        :return:
        """
        if self.flexible_benefit:
            self.education_benefit = 0