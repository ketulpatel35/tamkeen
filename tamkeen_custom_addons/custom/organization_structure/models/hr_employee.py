from odoo import models, api, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    @api.depends('job_id','job_id.parent_id','job_id.parent_id.employee_id')
    def _get_direct_reporting(self):
        for rec in self:
            if rec.job_id and rec.job_id.parent_id and \
                    rec.job_id.parent_id.employee_id:
                rec.parent_id = rec.job_id.parent_id.employee_id.id
                rec.reporting_to_required = True
            else:
                rec.parent_id = False
                rec.reporting_to_required = False

    personnel_area_id = fields.Many2one('personnel.area',
                                        string='Personnel Area', related='job_id.personnel_area_id')
    personnel_sub_area_id = fields.Many2one('personnel.area',
                                            string='Personnel Sub Area', related='job_id.personnel_sub_area_id')
    employee_group_id = fields.Many2one('hr.employee.group',
                                        string='Employee Group', related='job_id.employee_group_id')
    employee_sub_group_id = fields.Many2one('hr.employee.group',
                                            string='Employee Sub Group', related='job_id.employee_sub_group_id')
    parent_id = fields.Many2one('hr.employee', compute='_get_direct_reporting',
                                string='Direct Reporting To', store=True)
    department_id = fields.Many2one('hr.department', string='Organization Unit',
                                    related='job_id.department_id', store=True)
    hod_id = fields.Many2one('hr.employee', related='department_id.manager_id',
                             string='Head of Organization Unit', store=True)
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    job_template_id = fields.Many2one('hr.job.template', string='Job '
                                                                'Template',
                                      related='job_id.job_template_id',
                                      store=True)
    reporting_to_required = fields.Boolean(string='Reporting To Required', store=True)
    job_id = fields.Many2one('hr.job', string='Position')

    @api.multi
    def assigned_positions(self):
        self.ensure_one()
        context = dict(self._context)
        return {
            'name': 'Position',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.job',
            'target': 'current',
            'context': context,
            'domain': [('employee_id', 'in', self.ids),
                       ('vacant', '=', True)]
        }

    @api.onchange('department_id')
    def _onchange_department(self):
        return False