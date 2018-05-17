from odoo import models, api, fields


class HrLeaveLinkedAmendment(models.TransientModel):
    _name = 'hr.leave.linked.amendment'

    monthly_partition_ids = fields.One2many('hr.holidays.monthly.partition',
                                            'holiday_id', string='Monthly '
                                                                 'Partition',
                                            store=True)

    @api.model
    def default_get(self, fields_list):
        res = super(HrLeaveLinkedAmendment, self).default_get(fields_list)
        context = dict(self._context)
        montly_partition_lst = []
        if context and context.get('active_id'):
            holiday_rec = self.env['hr.holidays'].browse(context.get(
                'active_id'))
            montly_partition_lst.append((6, 0, holiday_rec.monthly_partition_ids.filtered(lambda
                                                               record:
                                                           not
                                                           record.amendment_created).ids))
            res.update({'monthly_partition_ids': montly_partition_lst})
        return res

    @api.multi
    def confirm_by_hr(self):
        context = dict(self._context)
        amendment_obj = self.env['hr.payslip.amendment']
        for rec in self:
            if context and context.get('active_id'):
                holiday_rec = self.env['hr.holidays'].browse(context.get(
                    'active_id'))
                for line in rec.monthly_partition_ids:
                    vals = {
                        'employee_id': holiday_rec.employee_id and holiday_rec.employee_id.id or
                                       False,
                        'amendment_hours': line.hours,
                        'reference_id': str(holiday_rec._name) + ',' + str(holiday_rec.id),
                        'calculation_based_on': 'days_hours',
                        'type': 'deduction',
                        'name': holiday_rec.name,
                        'corresponding_rule': 'unpaid',
                        'number_of_days': line.days,
                        'job_id': holiday_rec.employee_id.job_id and
                                  holiday_rec.employee_id.job_id.id or False,
                        'department_id': holiday_rec.employee_id.department_id and \
                                         holiday_rec.employee_id.department_id.id or False,
                        'org_unit_type': holiday_rec.employee_id.department_id and \
                                         holiday_rec.employee_id.department_id.org_unit_type,
                        'pay_period_id': line.payroll_period_id and
                                         line.payroll_period_id.id or False
                    }
                    line.write({'amendment_created': True,
                                'holiday_id': context.get('active_id')})
                    amendment_obj.create(vals)
