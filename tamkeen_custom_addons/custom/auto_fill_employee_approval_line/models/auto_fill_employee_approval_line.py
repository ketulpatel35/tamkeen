from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.onchange('service_manager_id')
    def onchange_service_manager_id(self):
        if self.service_manager_id:
            self.attendance_manager_id = self.service_manager_id.id
            self.loan_manager_id = self.service_manager_id.id
            self.overtime_manager_id = self.service_manager_id.id
            self.pr_manager_id = self.service_manager_id.id
            self.leave_manager_id = self.service_manager_id.id
            self.eos_manager_id = self.service_manager_id.id
            self.bt_manager_id = self.service_manager_id.id
            self.timesheet_manager_id = self.service_manager_id.id
            self.expense_manager_id = self.service_manager_id.id
            self.bp_manager_id = self.service_manager_id.id

    @api.onchange('service_vp_id')
    def onchange_service_vp_id(self):
        if self.service_vp_id:
            self.attendance_vp_id = self.service_vp_id.id
            self.loan_vp_id = self.service_vp_id.id
            self.overtime_vp_id = self.service_vp_id.id
            self.pr_vp_id = self.service_vp_id.id
            self.leave_vp_id = self.service_vp_id.id
            self.eos_vp_id = self.service_vp_id.id
            self.bt_vp_id = self.service_vp_id.id
            self.timesheet_vp_id = self.service_vp_id.id
            self.expense_vp_id = self.service_vp_id.id
            self.bp_vp_id = self.service_vp_id.id

    @api.onchange('service_ceo_id')
    def onchange_service_ceo_id(self):
        if self.service_ceo_id:
            self.attendance_ceo_id = self.service_ceo_id.id
            self.loan_ceo_id = self.service_ceo_id.id
            self.overtime_ceo_id = self.service_ceo_id.id
            self.pr_ceo_id = self.service_ceo_id.id
            self.leave_ceo_id = self.service_ceo_id.id
            self.eos_ceo_id = self.service_ceo_id.id
            self.bt_ceo_id = self.service_ceo_id.id
            self.timesheet_ceo_id = self.service_ceo_id.id
            self.expense_ceo_id = self.service_ceo_id.id
            self.bp_ceo_id = self.service_ceo_id.id
