from odoo import models, api, fields


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def _count_amendment_request(self):
        """
        :return:
        """
        for rec in self:
            amendment_req_count = self.env[
                'hr.payslip.amendment'].search_count([
                ('reference_id', '=', str(rec._name) + ',' + str(rec.id))])
            rec.amendment_request_count = amendment_req_count

    def search_amendment_request(self, operator, value):
        """
        :return:
        """
        rec_list = []
        for rec in self:
            amendment_req_count = self.env[
                'hr.payslip.amendment'].search_count([
                ('reference_id', '=', str(rec._name) + ',' + str(rec.id))])
            if amendment_req_count:
                rec_list.append(rec.id)
        return [('id', 'in', rec_list)]

    @api.multi
    def action_payslip_amendment_request(self):
        """
        Open Service Management
        :return:
        """
        res = self.env['ir.actions.act_window'].for_xml_id(
            'hr_payslip_amendment', 'action_payslip_amendment')
        domain = [('reference_id', '=', str(self._name) + ',' + str(self.id))]
        ctx = {'default_reference_id': str(self._name) + ',' + str(self.id),
               'default_employee_id': self.employee_id.id,
               'default_calculation_based_on': 'days_hours',
               'default_corresponding_rule': 'unpaid',
               'default_type': 'deduction',
               'default_name': self.name,
               }
        res['context'] = ctx
        res['domain'] = domain
        return res

    linked_with_payroll = \
        fields.Boolean(string='Linked With Payroll')
                       # related='holiday_status_id.linked_with_payroll')
    amendment_request_count = fields.Integer('Leave Request Count',
                                           store=False,
                                           compute='_count_amendment_request',
                                           search="search_amendment_request")

    @api.onchange('holiday_status_id')
    def onchange_holidays_status(self):
        """
        If there are no date set for date_to,
         automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        super(HrHolidays, self).onchange_holidays_status()
        if self.holiday_status_id \
                and self.holiday_status_id.linked_with_payroll:
            self.linked_with_payroll = \
                self.holiday_status_id.linked_with_payroll

    @api.multi
    def action_validate(self):
        res = super(HrHolidays, self).action_validate()
        amendment_obj = self.env['hr.payslip.amendment']
        if self.linked_with_payroll:
            vals = {
                'employee_id': self.employee_id and self.employee_id.id or
                               False,
                'amendment_hours': self.leaved_hours,
                'reference_id': str(self._name) + ',' + str(self.id),
                'calculation_based_on': 'days_hours',
                'type': 'deduction',
                'name': self.name,
                'corresponding_rule': 'unpaid',
                'number_of_days': self.real_days,
                'job_id': self.employee_id.job_id and
                          self.employee_id.job_id.id or False,
                'department_id': self.employee_id.department_id and \
                             self.employee_id.department_id.id or False,
                'org_unit_type': self.employee_id.department_id and \
                             self.employee_id.department_id.org_unit_type
            }
            # amendment_obj.create(vals)
        return res

    @api.multi
    def get_payslip_amendment(self):
        self.ensure_one()
        context = dict(self._context)
        return {
            'name': 'Payslip Amendment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.payslip.amendment',
            'target': 'current',
            'context': context,
            'domain': [('overtime_request_id', 'in', self.ids)]
        }