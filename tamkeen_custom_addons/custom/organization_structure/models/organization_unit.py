from odoo import models, fields, api, _


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _description = 'Organization Unit'

    _sql_constraints = [
        ('code_uniq', 'unique(short_name, company_id)',
         'Code should be unique per position!')]

    short_name = fields.Char(string='Short Name', traslate=True)
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    code = fields.Char(string='Code')
    parent_id = fields.Many2one('hr.department', string='Parent Organization Unit',
                                index=True)
    name = fields.Char('Name', required=True)
    jobs_ids = fields.One2many('hr.job', 'department_id', string='Position/s')
    holder_position_id = fields.Many2one('hr.job', string='Chief Position')
    # org_unit_owner_id = fields.Many2one('hr.employee',
    #                                             string='Head',
    #                                             related='holder_position_id.occupied_by_employee_id',
    #                                             store=True)
    position_count = fields.Integer(compute='_position_count',
                                    string='Related Position/s')
    manager_id = fields.Many2one('hr.employee',
                                                string='Head of Organization Unit',
                                                related='holder_position_id.employee_id',
                                                store=True)
    schedule_template_id = fields.Many2one('resource.calendar',
                                           string='Working Schedule Template')
    state = fields.Selection([('planned', 'Planned'), ('submitted',
                                                       'Submitted'),
                              ('rejected', 'Rejected'), ('approved',
                                                         'Approved'),
                               ('active', 'Active')], string='Status',
                             default='planned',
                             track_visibility='onchange', copy=False,
                             readonly=True, required=True)
    description = fields.Text(string='Description')
    department_staff = fields.Selection([('department', 'Department'),
                                         ('staff', 'Staff')],
                                        string='Department/Staff')
    org_unit_type = fields.Selection([ ('root', 'Root'), ('business',
                                                          'Business Unit'),
                                       ('department', 'Department'),
                                       ('section', 'Section')], 
                                     string='Organization Unit Type')

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        if vals:
            seq = self.env['ir.sequence'].next_by_code('hr.department')
            vals.update({'code': seq})
        res = super(HrDepartment, self).create(vals)
        return res

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id:
            self.schedule_template_id = \
                self.parent_id.schedule_template_id

    @api.multi
    def related_positions(self):
        context = dict(self._context)
        self.ensure_one()
        return {
            'name': 'Position',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.job',
            'target': 'current',
            'context': context,
            'domain': [('department_id', 'in', self.ids)]
        }

    @api.multi
    def _position_count(self):
        for rec in self:
            rec.position_count = self.env['hr.job'].search_count(
                [('department_id', '=', rec.id)])

    @api.model
    def default_get(self, fields_list):
        res = super(HrDepartment, self).default_get(fields_list)
        if self._context:
            if self._context.get('active_id') and self._context.get(
                    'active_model') == 'hr.department':
                res.update({'parent_id': self._context.get(
                    'active_id')})
        return res

    @api.multi
    def related_line_manager_of(self):
        context = dict(self._context)
        self.ensure_one()
        return {
            'name': 'Organization Unit',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.department',
            'target': 'current',
            'context': context,
            'domain': [('parent_id', 'in', self.ids)]
        }

    @api.multi
    def submit_for_approval(self):
        for rec in self:
            rec.write({'state':'submitted'})

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
