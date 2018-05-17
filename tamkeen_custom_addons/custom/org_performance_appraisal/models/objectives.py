from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import Warning


class PaObjectives(models.Model):
    _name = 'pa.objectives'
    _rec_name = 'employee_id'
    _description = 'Objectives'

    employee_id = fields.Many2one(
        'hr.employee', "Employee", required=True,
        default=lambda self: self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id)], limit=1))
    employee_company_id = fields.Char(string='Employee ID', readonly=True)
    job_id = fields.Many2one('hr.job', 'Position')
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id, string='Company')
    department_id = fields.Many2one(
        'hr.department', string='Organization Unit', copy=False)
    org_unit_type = fields.Selection([
        ('root', 'Root'), ('business', 'Business Unit'),
        ('department', 'Department'), ('section', 'Section')],
        string='Organization Unit Type', copy=False)
    # calendar_year = fields.Char('Calendar Year', copy=False,
    #                             default=datetime.today().year)
    locked_by_hr = fields.Boolean('Locked by HR')
    goal = fields.Text('Goal', copy=False)
    weightage = fields.Float('Weightage(%)', copy=False)
    measurement = fields.Text('Measurement', copy=False)
    target_date = fields.Date('Target Date', copy=False)
    actual_date = fields.Date('Actual Date', copy=False)
    completed = fields.Float('Completed(%)', copy=False)
    status = fields.Selection([
        ('in_progress', 'In Progress'), ('On Hold', 'on_Hold'),
        ('closed', 'Closed')], 'Status', default='in_progress')
    objectives_line_ids = fields.One2many(
        'pa.objectives.line', 'objectives_id', 'Actions', copy=False,
        ondelete="cascade")
    note = fields.Text('Note', copy=False)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
        Onchange Employee Id
        :return:
        """

        if self.employee_id:
            self.employee_company_id = self.employee_id.f_employee_no
            self.job_id = self.employee_id.job_id and \
                          self.employee_id.job_id or False
            self.department_id = self.employee_id.department_id and \
                                 self.employee_id.department_id.id or False
            self.org_unit_type = self.employee_id.department_id and \
                                 self.employee_id.department_id.org_unit_type

    @api.multi
    def get_manager_objective(self):
        """
        Employee see the list of manager objective
        :return:
        """
        if not self.employee_id.parent_id:
            raise Warning(_("The employee profile isn't linked with a correct "
                            "reporting line, Kindly contact the HR team for "
                            "support."))
        objective_rec = self.env['pa.objectives'].search([
            ('employee_id', '=', self.employee_id.parent_id.id)])
        return {
            'name': _('Manager Objective/s'),
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'pa.objectives',
            'view_id': self.env.ref(
                'org_performance_appraisal.manager_objective_tree').id,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', objective_rec.ids)],
        }


class PaObjectivesLine(models.Model):
    _name = 'pa.objectives.line'
    _description = 'Objectives Line'

    name = fields.Char('Name')
    description = fields.Text('Description')
    objectives_id = fields.Many2one('pa.objectives', 'Objectives')


class PaObjectivesAssessment(models.Model):
    _name = 'pa.objectives.assessment'
    _description = 'Objectives Assessment'

    @api.depends('manager_assessment', 'weightage')
    def _compute_evaluation_value(self):
        """
        evaluation value calculation
        :return:
        """
        for rec in self:
            evaluation_value = 0.0
            if rec.weightage and rec.manager_assessment and \
                    rec.manager_assessment.points:
                evaluation_value = \
                    rec.weightage * rec.manager_assessment.points
            rec.evaluation_value = evaluation_value

    goal = fields.Text('Goal', copy=False)
    weightage = fields.Float('Weightage(%)', copy=False)
    measurement = fields.Text('Measurement', copy=False)
    target_date = fields.Date('Target Date', copy=False)
    actual_date = fields.Date('Actual Date', copy=False)
    completed = fields.Float('Completed(%)', copy=False)
    status = fields.Selection([
        ('in_progress', 'In Progress'), ('done', 'Done'),
        ('On Hold', 'on_Hold')], 'Status', default='in_progress')
    self_assessment = fields.Many2one('rating.scale', 'Self Assessment')
    manager_assessment = fields.Many2one('rating.scale', 'Manager Assessment')
    evaluation_value = fields.Float(
        'Evaluation Value', compute='_compute_evaluation_value', store=True,
        help='Evaluation Value = Weightage * Manager Assessment.Points')
    performance_appraisal_id = fields.Many2one(
        'performance.appraisal', 'Performance Appraisal')
