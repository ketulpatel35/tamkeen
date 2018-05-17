# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import fields, models


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    service_manager_id = fields.Many2one('hr.employee',
                                         string='Service Manager',
                                         help='The responsible person for '
                                              'approving this employee '
                                              'services as a manager.')
    service_vp_id = fields.Many2one('hr.employee',
                                    string='VP (Service Approval)',
                                    help='The responsible person for '
                                    'approving this employee '
                                    'services as a VP.')
    service_ceo_id = fields.Many2one('hr.employee',
                                     string='CEO (Service Approval)',
                                     help='The responsible person for '
                                          'approving this employee '
                                          'services as a CEO.')

    # @api.model
    # def create(self, vals):
    #     vp_role = False
    #     service_manager_id, service_vp_id,
    #  service_ceo_id = False, False, False
    #     # if context is None:
    #     #     context = {}
    #     parent_id = vals.get('parent_id', False)
    #     if parent_id:
    #         # employee_pool = self.pool.get('hr.employee')
    #         parent_employee = self.browse(parent_id)
    #         if parent_employee.employee_role == 'director':
    #             # employee_parent_obj = \
    #             # employee_pool.browse(cr, uid, parent_employee.id)[0]
    #             while not vp_role:
    #                 if parent_employee and parent_employee.employee_role in \
    #                         ['vp', 'ceo']:
    #                     service_vp_id = parent_employee.id
    #                     service_ceo_id = parent_employee.parent_id.id
    #                     vp_role = True
    #                 else:
    #                     if parent_employee and parent_employee.parent_id:
    #                         parent_employee = parent_employee.parent_id[
    #                             0] or False
    #             service_manager_id = parent_employee.id
    #             if not service_vp_id:
    #                 service_vp_id = parent_employee.id
    #             service_ceo_id = service_ceo_id
    #         elif parent_employee.employee_role == 'vp':
    #             service_manager_id = parent_employee.id
    #             service_vp_id = parent_employee.id
    #             service_ceo_id = parent_employee.parent_id.id
    #
    #         elif parent_employee.employee_role == 'ceo':
    #             service_manager_id = parent_employee.id
    #             service_vp_id = parent_employee.id
    #             service_ceo_id = parent_employee.id
    #
    #     vals.update({'service_manager_id': service_manager_id,
    #                  'service_vp_id': service_vp_id,
    #                  'service_ceo_id': service_ceo_id,
    #                  })
    #
    #     return super(hr_employee, self).create(vals)
