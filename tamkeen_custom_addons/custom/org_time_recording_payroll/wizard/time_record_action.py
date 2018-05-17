from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from odoo.exceptions import Warning


class TimeRecordActionWizard(models.TransientModel):
    """Time Record Action wizard."""

    _name = "time.record.action.wizard"
    _description = "Time Record Action Wizard"

    payroll_period_id = fields.Many2one('hr.payroll.period',
                                        'Payroll Period')

    @api.model
    def default_get(self, default_fields):
        res = super(TimeRecordActionWizard, self).default_get(default_fields)
        payroll_period_obj = self.env['hr.payroll.period']
        today_date = datetime.today()
        first_date_of_month = today_date.replace(day=1)
        lastMonth_date = first_date_of_month - timedelta(days=1)
        latest_payroll_period_id = payroll_period_obj.search([
            ('state', 'in', ('open', 'ended')), ('date_start', '>=',
                                                 str(lastMonth_date))],
            order="date_start",
            limit=1)
        res.update({'payroll_period_id': latest_payroll_period_id.id})
        return res

    @api.multi
    def button_confirm(self):
        context = dict(self._context)
        time_recording_line_obj = self.env['sheet.time.recording.line']
        active_ids = context.get('active_ids')
        for line in \
                time_recording_line_obj.browse(active_ids):
            if line.state in ('draft', 'on_hold', 'simulated', 'new_joiner'):
                line.with_context({'state': 'confirm'}).add_stage_log()
                line.write({'previous_state': line.state})
                line.write({'state': 'confirm'})

    @api.multi
    def button_assign_to_payroll(self):
        context = dict(self._context)
        time_recording_line_obj = self.env['sheet.time.recording.line']
        active_ids = context.get('active_ids')
        time_date = ''
        for rec in self:
            for line in time_recording_line_obj.browse(active_ids):
                if line.state != 'confirm':
                    time_date += str(line.date) + ', '
            if time_date:
                raise Warning(_('You need to first confirm time records. '
                                'Kindly, Check bellow dates time records.\n '
                                '%s')
                              % time_date)
            for line in time_recording_line_obj.browse(active_ids):
                if line.state == 'confirm':
                    line.with_context({'state': 'assign_to_payroll'}).add_stage_log()
                    line.write({'previous_state': line.state})
                    line.write(
                        {'state': 'assign_to_payroll', 'payroll_locked': True,
                         'payroll_locked_date': date.today()})
            rec.payroll_period_id.write({'last_lock_date': date.today()})

    @api.multi
    def button_on_hold(self):
        context = dict(self._context)
        time_recording_line_obj = self.env['sheet.time.recording.line']
        active_ids = context.get('active_ids')
        time_date = ''
        for line in time_recording_line_obj.browse(active_ids):
            if line.state not in ('confirm', 'draft'):
                time_date += str(line.date) + ', '
        if time_date:
            raise Warning(_('You need to first confirm time records. '
                            'Kindly, Check bellow dates time records.\n %s')
                          % time_date)
        for line in time_recording_line_obj.browse(active_ids):
            line.with_context({'state': 'on_hold'}).add_stage_log()
            line.write({'previous_state': line.state})
            line.write({'state': 'on_hold'})

    @api.multi
    def button_unlock(self):
        context = dict(self._context)
        time_recording_line_obj = self.env['sheet.time.recording.line']
        active_ids = context.get('active_ids')
        for line in time_recording_line_obj.browse(active_ids):
            line.with_context({'state': line.previous_state}).add_stage_log()
            line.write({'state': line.previous_state})
            # line.write({'previous_state': line.state})