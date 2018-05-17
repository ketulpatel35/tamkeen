from odoo import models, api, fields, _


class HrJobTemplate(models.Model):
    _name = 'hr.job.template'
    _description = 'HR Job Template'
    _inherit = ['mail.thread']

    name = fields.Char(string='Job Template Name', traslate=True, track_visibility='onchange')
    code = fields.Char(string='Code')
    short_name = fields.Char(string='Short Name', traslate=True, track_visibility='onchange')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    position_count = fields.Integer(compute='_position_count',
                                    string='Related Position/s')
    department_staff = fields.Selection([('department', 'Department'),
                                         ('staff', 'Staff')],
                                        string='Department/Staff')
    employee_group_id = fields.Many2one('hr.employee.group',
                                        string='Employee Group')
    employee_sub_group_id = fields.Many2one('hr.employee.group',
                                            string='Employee Sub Group')
    description = fields.Text(string='Description')
    requirements = fields.Text(string='Requirements')
    duties = fields.Text(string='Duties')
    state = fields.Selection([('planned', 'Planned'), ('submitted',
                                                       'Submitted'),
                              ('rejected', 'Rejected'), ('approved',
                                                         'Approved'),
                              ('active', 'Active')], string='Status',
                             default='planned',
                             track_visibility='onchange', copy=False,
                             readonly=True, required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, index=True,
                                 default=lambda self: self.env.user.company_id,
                                 help="Company related to user.")

    _sql_constraints = [
        ('code_uniq', 'unique(short_name, company_id)',
         'Code should be unique per position!')]

    @api.multi
    def related_positions(self):
        self.ensure_one()
        context = dict(self._context)
        return {
            'name': 'Position',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.job',
            'target': 'current',
            'context': context,
            'domain': [('job_template_id', 'in', self.ids)]
        }

    @api.multi
    def _position_count(self):
        for rec in self:
            rec.position_count = self.env['hr.job'].search_count(
                [('job_template_id', '=', rec.id)])

    @api.multi
    def submit_for_approval(self):
        for rec in self:
            rec.write({'state': 'submitted'})

    @api.multi
    def button_approved(self):
        for rec in self:
            rec.write({'state': 'approved'})

    @api.multi
    def button_rejected(self):
        for rec in self:
            rec.write({'state': 'rejected'})

    @api.multi
    def button_active(self):
        for rec in self:
            rec.write({'state': 'active'})