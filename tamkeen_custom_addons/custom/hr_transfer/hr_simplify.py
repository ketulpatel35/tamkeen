# -*- coding:utf-8 -*-

from odoo import fields, api, models, _


class hr_employee(models.Model):

    """Simplified Employee Record Interface."""

    _name = 'hr.employee'
    _inherit = 'hr.employee'

    # job_id = fields.Many2one('hr.job', related='contract_id.job_id',
    #                          string="Job",
    #                          method=True, readonly=True, store=True)

    _sql_constraints = [
        ('unique_identification_id', 'unique(identification_id)',
         _('Official Identifications must be unique!')),
    ]

    @api.model
    def default_get(self, fields):
        res = super(hr_employee, self).default_get(fields)
        cid = self.env['res.country'].search([('code', '=', 'ET')], limit=1)
        if cid:
            res.update({'country_id': cid.id})
        return res


class hr_contract(models.Model):

    _inherit = 'hr.contract'

    @api.multi
    def _get_department_name(self):
        for rec in self:
            if not rec.end_job_id.id:
                rec.employee_dept_name = rec.job_id.department_id.name
            else:
                rec.employee_dept_name = rec.end_job_id.department_id.name

    @api.multi
    def _get_job_name(self):
        for rec in self:
            if not rec.end_job_id.id:
                rec.employee_job_name = rec.job_id.name
            else:
                rec.employee_job_name = rec.end_job_id.name

    employee_dept_id = fields.Many2one('hr.department',
                                       related='employee_id.department_id',
                                       string="Default Dept Id")
    employee_dept_name = fields.Char(compute='_get_department_name',
                                     string="Default Dept Name")
    employee_job_name = fields.Char(compute='_get_job_name',
                                    string="Default Job Name")

    @api.model
    def default_get(self, fields):
        res = super(hr_contract, self).default_get(fields)
        e_ids = self._context.get('search_default_employee_id', False)
        if e_ids:
            res.update({'employee_id': e_ids})
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):

        super(hr_contract, self)._onchange_employee_id()
        dom = {
            'job_id': [],
        }
        if self.employee_id:
            dom['job_id'] = [('department_id', '=',
                              self.employee_id.department_id.id)]
            # self.employee_dept_id = self.employee_id.department_id.id
        return {'domain': dom}
