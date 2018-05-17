from odoo import models, fields


class UserAllocation(models.Model):
    _name = 'multi.user.allocation'
    _rec_name = 'allowed_user'

    allowed_user = fields.Many2one('res.users', 'Allowed User')
    allowed_bypass = fields.Boolean('Allowed Delegate')
    active_delegate = fields.Boolean('Active Delegate User')
    delegate_user = fields.Many2one('res.users', 'Delegate User')
    stage_config_id = fields.Many2one('stage.config', 'Stage Config Id')
    department_id = fields.Many2one('hr.department', string="Department")

    # employee_id = fields.Many2one('hr.employee', 'Employee')

    # dam_conf_line_ids = fields.Many2one('dam.conf.line', 'DAM Conf Line')

    # @api.onchange('allowed_user')
    # def _onchange_allowed_user(self):
    #     """
    #     :return:
    #     """
    #     if self.allowed_user:
    #         emp_rec = self.env['hr.employee'].search([
    #             ('user_id', '=', self.allowed_user.id)], limit=1)
    #         if emp_rec:
    #             self.employee_id = emp_rec.id
