# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models
from odoo.tools.translate import _
import logging

_l = logging.getLogger(__name__)


class hr_job(models.Model):
    _name = 'hr.job'
    _inherit = 'hr.job'

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

    @api.multi
    def _get_all_child_ids(self):
        for rec in self:
            rec.all_child_ids = self.search([('parent_id', 'child_of',
                                              rec.id)])

    # overwite the default method
    @api.multi
    def _compute_application_count(self):
        for rec in self:
            read_group_result = self.env['hr.applicant'].read_group([(
                'job_id', '=', rec.id)], ['job_id'], ['job_id'])
            result = dict((data['job_id'][0], data['job_id_count']) for data in
                          read_group_result)
            rec.application_count = result.get(rec.id, 0)

    department_manager = fields.Boolean(string='Department Manager')
    parent_id = fields.Many2one('hr.job', string='Immediate Superior',
                                ondelete='cascade')
    child_ids = fields.One2many('hr.job', 'parent_id',
                                string='Immediate Subordinates')
    all_child_ids = fields.Many2many('hr.job', 'hr_job_rel', 'src_hr_job',
                                     'dest_hr_job',
                                     compute='_get_all_child_ids',
                                     String='test')
    parent_left = fields.Integer(string='Left Parent', index=True)
    parent_right = fields.Integer(string='Right Parent', index=True)

    @api.multi
    def _check_recursion(self):
        # Copied from product.category
        # This is a brute-force approach to the problem, but
        # should be good enough.
        level = 100
        while len(self._ids):
            self._cr.execute(
                'select distinct parent_id from hr_job where id IN %s',
                (tuple(self._ids),))
            self._ids = filter(None, map(lambda x: x[0],
                                         self._cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion,
         _('Error!\nYou cannot create recursive jobs.'), ['parent_id']),
    ]

    @api.multi
    def write(self, vals):
        res = super(hr_job, self).write(vals)
        dept_obj = self.env['hr.department']
        for job in self:
            dept_id = False
            if vals.get('department_manager', False):
                if vals.get('department_id', False):
                    dept_id = vals['department_id']
                else:
                    dept_id = job.department_id.id
                dept_rec = dept_obj.browse(dept_id)
                employee_id = False
                for ee in job.employee_ids:
                    employee_id = ee.id
                if employee_id:
                    dept_rec.manager_id = employee_id
            elif vals.get('department_id', False):
                dept_id = vals['department_id']
                dept_rec = dept_obj.browse(dept_id)
                if job.department_manager:
                    employee_id = False
                    for ee in job.employee_ids:
                        employee_id = ee.id
                    dept_rec.manager_id = employee_id
            elif vals.get('parent_id', False):
                parent_job = self.browse(vals['parent_id'])
                for parent_emp_rec in parent_job.employee_ids:
                    for job_emp_rec in job.employee_ids:
                        job_emp_rec.parent_id = parent_emp_rec.id
        return res


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    @api.model
    def create(self, vals):
        res = super(hr_contract, self).create(vals)
        if not vals.get('job_id', False):
            return res

        ee_obj = self.env['hr.employee']
        job = self.env['hr.job'].browse(vals['job_id'])

        # Write the employee's manager
        if job and job.parent_id:
            parent_id = False
            for ee in job.parent_id.employee_ids:
                parent_id = ee.id
            if parent_id and vals.get('employee_id'):
                emp_rec = ee_obj.browse(vals['employee_id'])
                emp_rec.parent_id = parent_id

        # Write any employees with jobs that are immediate descendants of this
        # job
        if job:
            job_child_ids = []
            [job_child_ids.append(child.id) for child in job.child_ids]
            if len(job_child_ids) > 0:
                ee_ids = ee_obj.search([('job_id', 'in', job_child_ids)])
                if len(ee_ids) > 0:
                    parent_id = False
                    for ee in job.employee_ids:
                        parent_id = ee.id
                    if parent_id:
                        ee_ids.parent_id = parent_id
        return res

    @api.multi
    def write(self, vals):
        res = super(hr_contract, self).write(vals)
        if not vals.get('job_id', False):
            return res

        ee_obj = self.env['hr.employee']
        job = self.env['hr.job'].browse(vals['job_id'])

        # Write the employee's manager
        if job and job.parent_id:
            parent_id = False
            for ee in job.parent_id.employee_ids:
                parent_id = ee.id
            if parent_id:
                for contract in self:
                    contract.employee_id.parent_id = parent_id

        # Write any employees with jobs that are immediate descendants of this
        # job
        if job:
            job_child_ids = []
            [job_child_ids.append(child.id) for child in job.child_ids]
            if len(job_child_ids) > 0:
                ee_ids = ee_obj.search([('job_id', 'in', job_child_ids),
                                        ('active', '=', True)])
                if len(ee_ids) > 0:
                    parent_id = False
                    for ee in job.employee_ids:
                        parent_id = ee.id
                    if parent_id:
                        ee_ids.parent_id = parent_id
        return res
