# -*- coding: utf-8 -*-

from odoo import fields, models, api


class default_employee_approval_line(models.TransientModel):
    _name = "default.employee.approval.line"
    name = fields.Char(string='Name')

    @api.multi
    def action_fix_directors_roles(self):
        employee_pool = self.env['hr.employee']
        employee_ids = employee_pool.search([('active', '=', True)])
        for employee in employee_ids:
            employee_role = 'staff'
            if employee.manager:
                employee_role = 'director'
            employee.employee_role = employee_role

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'default.employee.approval.line',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.one
    def _get_employee_approval_line(self, employee):
        # vp_role = False
        service_manager_id, service_vp_id, service_ceo_id = False, False, False
        if employee.parent_id:
            if employee.parent_id.employee_role == 'director':
                service_manager_id = employee.parent_id.id
                service_vp_id = employee.parent_id.parent_id.id
                service_ceo_id = employee.parent_id.parent_id.id

            elif employee.parent_id.employee_role == 'vp':
                service_manager_id = employee.parent_id.id
                service_vp_id = employee.parent_id.id
                service_ceo_id = employee.parent_id.parent_id.id

            elif employee.parent_id.employee_role == 'ceo':
                service_manager_id = employee.parent_id.id
                service_vp_id = employee.parent_id.id
                service_ceo_id = employee.parent_id.parent_id.id

            elif employee.employee_role == 'vp':
                service_manager_id = employee.parent_id.id
                service_vp_id = employee.id
                service_ceo_id = employee.parent_id.id

            elif employee.employee_role == 'ceo':
                service_manager_id = employee.id
                service_vp_id = employee.id
                service_ceo_id = employee.id

        return {'service_manager_id': service_manager_id,
                'service_vp_id': service_vp_id,
                'service_ceo_id': service_ceo_id}

    @api.multi
    def action_reset_default_employee_approval_line(self):
        employee_pool = self.env['hr.employee']
        employee_ids = employee_pool.search([('active', '=', True)])
        for employee in employee_ids:
            employee_approval_line = self._get_employee_approval_line(employee)
            employee.write(employee_approval_line)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'default.employee.approval.line',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
