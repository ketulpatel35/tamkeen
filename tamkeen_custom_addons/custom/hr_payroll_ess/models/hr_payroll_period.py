from odoo import models, fields, api, _
# from odoo.exceptions import Warning


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    display_in_ess = fields.Boolean(string='Display In Ess')


# class payroll_period_end_1(models.Model):
    # _inherit = 'hr.payroll.period.end.1'
    #
    #
    # @api.multi
    # def button_display_in_ess(self):
    #     self.ensure_one()
    #     # count = 0
    #     period_id = self._context.get('active_id', False)
    #     if not period_id:
    #         return {'type': 'ir.actions.act_window_close'}
    #     period_rec = self.env['hr.payroll.period'].browse(period_id)
    #     if period_rec.state != 'generate':
    #         return {'type': 'ir.actions.act_window_close'}
    #     for run_id in period_rec.register_id.run_ids:
    #         for slip_id in run_id.slip_ids:
    #             slip_id.display_in_ess = True
    #     #         count += 1
        # raise Warning(_('The number of successfully displayed payslip/s in '
        #                 'the ESS: %s')% count)


