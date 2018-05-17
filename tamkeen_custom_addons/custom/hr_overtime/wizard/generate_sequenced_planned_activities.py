from odoo import models, api, fields, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning


class GenerateSequencedPlannedActivitiesWizard(models.TransientModel):
    _name = 'generate.sequence.planned.activities'
    _description = 'Generate Sequenced Planned Activities'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    activity_planned = fields.Text('Activity')
    expected_hours = fields.Float('Expected Hours(Overtime)')
    remark = fields.Text('Remarks')

    def _check_expected_hours(self):
        if self.expected_hours <= 0:
            raise Warning(_('Expected hours should be greater than 0.'))
        return True

    @api.multi
    def generate_sequenced_planned_activities(self):
        context = dict(self._context)
        pre_request_obj = self.env['overtime.pre.request']
        pre_request_line_obj = self.env['overtime.planned.activity']
        if context and context.get('active_id'):
            active_rec = pre_request_obj.browse(context.get(
                'active_id'))
            for rec in self:
                rec._check_expected_hours()
                active_rec.plan_activity_ids.unlink()
                overtime_claim_request_list = []
                current_date = fields.Date.from_string(rec.start_date)
                diff_days = (fields.Date.from_string(rec.end_date) -
                             current_date).days + 1
                for line in range(diff_days):
                    context.update(
                        {'r_date': fields.Date.to_string(current_date),
                         'expected_hours': rec.expected_hours,
                         'pre_request_policy_id':
                             active_rec.pre_approval_policy_id})
                    day_cost = \
                        pre_request_line_obj.with_context(
                            context).calculate_day_cost()
                    overtime_claim_request_list.append((0, 0, {
                        'date': current_date,
                        'activity_planned': rec.activity_planned,
                        'expected_hours': rec.expected_hours,
                        'day_cost': day_cost,
                        'remark': rec.remark
                    }))
                    current_date += relativedelta(days=1)
                active_rec.plan_activity_ids = overtime_claim_request_list
                active_rec.check_maximum_hours(
                    active_rec.pre_approval_policy_id,
                    active_rec.plan_activity_ids)
