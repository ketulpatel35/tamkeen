from odoo import models, api, fields, _
from odoo.exceptions import Warning
from datetime import date


class HrApplocant(models.Model):
    _inherit = 'hr.applicant'

    hire_action_id = fields.Many2one('personnel.actions', string='Hire Action')

    @api.multi
    def hire_employee(self):
        personnel_action_type_obj = self.env['personnel.action.type']
        personnel_action_obj = self.env['personnel.actions']
        personnel_action_reason_obj = self.env['reason.for.action']
        personnel_action_type_rec = personnel_action_type_obj.search([(
            'code', '=', 'HIRE')], limit=1)
        personnel_action_reason_rec = personnel_action_reason_obj.search([(
            'code', '=', 'FNP')], limit=1)
        if not personnel_action_type_rec:
            raise Warning(_('System should have Hire type action.'))
        vals = {'action_type_id': personnel_action_type_rec.id,
                'reason_action_id': personnel_action_reason_rec and
                                    personnel_action_reason_rec.id or False,
                'date_from': date.today()}
        for rec in self:
            if rec.emp_id:
                personnel_action_rec = personnel_action_obj.search([(
                    'action_type_id.code', '=',
                                              'HIRE'), ('employee_id', '=',
                                                        rec.emp_id.id)],
                    limit=1)
                if len(personnel_action_rec) > 0:
                    raise Warning(_('Already there is a hire action %s for '
                                    'that employee %s.')%(
                        personnel_action_rec.name, rec.emp_id.name))
                else:
                    vals.update({'employee_id': rec.emp_id.id,
                                 'new_position_id': rec.job_id.id})
                    new_personnel_action_rec = personnel_action_obj.create(
                        vals)
                    rec.write({'hire_action_id':
                                   new_personnel_action_rec.id})
            else:
                raise Warning(_('Kindly, To proceed with this action, the applicant should be linked to a profile.'))
        return True

