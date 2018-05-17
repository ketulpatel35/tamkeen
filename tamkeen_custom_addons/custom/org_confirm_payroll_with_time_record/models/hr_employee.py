from odoo import models, api, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = dict(self._context) or {}
        skip_employee_lst = []
        if context.get('active_id') and str(context.get(
                'active_model')) == 'hr.payslip.run':
            batch_rec = self.env['hr.payslip.run'].\
                browse(context.get('active_id'))
            for payslip in batch_rec.slip_ids:
                skip_employee_lst.append(payslip.employee_id.id)
            args.append(('id', 'not in', skip_employee_lst))
        return super(HrEmployee, self).search(args, offset, limit, order,
                                              count=count)