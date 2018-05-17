# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def compute_work_resumption(self):
        """
        :return:
        """
        for rec in self:
            rec.count_work_resumption = len(rec.work_resumption_ids.ids)

    @api.multi
    def _get_work_resumption_id(self):
        for rec in self:
            rec.work_resumption_id = self.env['work.resumption'].search(
                [('hr_holiday_id', '=', rec.id)], limit=1, order='id desc')

    work_resumption_done = fields.Boolean(string='Work Resumption Done')
    is_work_resumption = fields.Boolean(
        string='Is Work Resumption')

    work_resumption_ids = fields.One2many('work.resumption',
                                          'hr_holiday_id', 'Work Resumptions')
    count_work_resumption = fields.Integer(compute='compute_work_resumption')
    work_resumption_id = fields.Many2one(
        'work.resumption', string='Work Resumption')

    @api.multi
    def button_cancel(self):
        res = super(HrHolidays, self).button_cancel()
        for rec in self:
            resumption_rec = self.env['work.resumption'].search(
                [('hr_holiday_id', '=', rec.id)])
            for resumption in resumption_rec:
                resumption.unlink()
        return res

    @api.multi
    def button_work_resumption(self):
        """
        work resumption smart button (display record in tree view)
        :return:
        """
        res_id = False
        if self.work_resumption_id:
            res_id = self.work_resumption_id
        else:
            res_id = self.env['work.resumption'].search([
                ('hr_holiday_id', '=', self.id)], limit=1, order='id desc')
        self.ensure_one()
        return {
            'name': _('Work Resumption'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'work.resumption',
            'res_id': res_id.id,
        }

    @api.multi
    def get_leave_summary_report(self):
        """
        leave summary report
        :return:
        """
        self.ensure_one()
        view_id = self.env['ir.model.data'].get_object_reference(
            'employee_leave_summary', 'employee_leave_summary_tree_view')[1]
        if self.holiday_status_id and self.employee_id:
            domain = [('holiday_status_id', '=', self.holiday_status_id.id),
                      ('employee_id', '=', self.employee_id.id)]
            return {
                'name': _('Leave Summary'),
                'type': 'ir.actions.act_window',
                'view_type': 'tree',
                'view_mode': 'form',
                'res_model': 'employee.leave.summary',
                'views': [(view_id, 'tree')],
                'view_id': view_id,
                'domain': domain,
            }
