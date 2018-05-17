from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT
from odoo.exceptions import Warning


class HrPayrollPeriod(models.Model):
    _name = 'hr.payroll.period'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Description')
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date')
    last_lock_date = fields.Date(string='Last Lock Date',
                                 track_visibility='onchange')
    last_payroll_run_date = fields.Date(string='Last Payroll Run Date',
                                        track_visibility='onchange')
    state = fields.Selection([('open', 'Open'),
                              ('ended', 'End of Period Processing'),
                              ('locked', 'Locked'),
                              ('generate', 'Generating Payslips'),
                              ('payment', 'Payment'),
                              ('closed', 'Closed')],
                             string='State', index=True,
                             default='open')

    _order = "date_start desc"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ctx = self._context
        if 'order_display' in ctx:
            order = ctx['order_display']
        res = super(HrPayrollPeriod, self).search(
            args, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.model
    def try_create_new_period(self):
        month_of_the_year = 13
        today_date = datetime.now().strftime(OE_DATETIMEFORMAT)
        convert_today_date = datetime.strptime(today_date, OE_DATETIMEFORMAT)
        current_month_start_date = convert_today_date + relativedelta(day=1,
                                                                      month=1,
                                           year=convert_today_date.year,
                                                                      hour=0,
                                                                      minute=0,
                                                                      second=0)
        for start_month in range(1, month_of_the_year):
            next_month_start_date = current_month_start_date + \
                                    relativedelta(months=1)
            current_month_end_date = next_month_start_date - relativedelta(
                days=1, hour=20, minute=59, second=59)
            period_rec = self.search([('date_start', '>=',
                                       str(current_month_start_date)),
                                      ('date_end', '<=',
                                       str(current_month_end_date))], limit=1)
            if period_rec:
                continue
            vals = {
                'date_start': current_month_start_date,
                'date_end': current_month_end_date,
                'name': 'Payroll Period for %s' %
                        current_month_start_date.strftime("%b")

            }
            current_month_start_date = next_month_start_date
            self.create(vals)

    @api.multi
    def set_state_closed(self):
        for rec in self:
            rec.state = 'closed'


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payroll_period_id = fields.Many2one('hr.payroll.period',
                                    string='Payroll Period')

    date_from = fields.Date(string='Date From', readonly=True, required=True)
    date_to = fields.Date(string='Date To', readonly=True, required=True)

    @api.model
    def default_get(self, default_fields):
        res = super(HrPayslip, self).default_get(default_fields)
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

    @api.onchange('payroll_period_id')
    def onchange_payroll_period(self):
        self.date_from = False
        self.date_to = False
        if self.payroll_period_id:
            date_from = self.payroll_period_id.date_start
            date_to = self.payroll_period_id.date_end
            self.date_from = datetime.strptime(date_from,
                                               OE_DATETIMEFORMAT).date()
            self.date_to = datetime.strptime(date_to, OE_DATETIMEFORMAT).date()

    @api.model
    def create(self, vals):
        if 'payroll_period_id' in self.env.context:
            vals['payroll_period_id'] = self.env.context.get(
                'payroll_period_id')
        return super(HrPayslip, self).create(vals)


class hr_payslip_amendment(models.Model):
    _inherit = 'hr.payslip.amendment'

    pay_period_id = fields.Many2one('hr.payroll.period',
                                    string='Start Pay Period',
                                    required=False,
                                    domain=[('state', 'in',
                                             ['open', 'ended', 'locked',
                                              'generate'])])

    batch = fields.Boolean(string='Batch')
    parent_id = fields.Many2one('hr.payslip.amendment',
                                string='Parent Amendment')

    end_period_id = fields.Many2one('hr.payroll.period',
                                    string='End Pay Period',
                                    domain=[('state', 'in',
                                             ['open', 'ended', 'locked',
                                              'generate'])])

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id is not False:
            self.installment = False

    @api.multi
    def get_next_period(self, date):
        next_period =\
            self.env['hr.payroll.period']\
                .search([('date_end', '>', date)], limit=1)
        return next_period

    @api.multi
    def do_generate(self):
        for amendment in self:
            if not amendment.batch and amendment.parent_id:
                raise Warning(_("You cannot generate"
                                " the Amendment because"
                                " it's linked to a batch"))
            if not amendment.pay_period_id or not amendment.end_period_id:
                return True
            if amendment.pay_period_id\
                    >= amendment.end_period_id:
                raise Warning(_('The start period'
                                ' must be anterior to the end period'))
            start_date = amendment.pay_period_id.date_end
            start_date_a = \
                datetime.strptime(start_date, OE_DATETIMEFORMAT)
            end_date = amendment.end_period_id.date_end
            end_date_a = \
                datetime.strptime(end_date, OE_DATETIMEFORMAT)
            months_diff = relativedelta(end_date_a, start_date_a).months
            start_period = amendment.pay_period_id.id
            for amendment_create in range(months_diff):
                end_period = amendment.get_next_period(start_date)
                if start_period and end_period:
                    create_amendment = self.copy()
                    create_amendment.write({'pay_period_id': end_period.id,
                                            'end_period_id': False,
                                            'parent_id': amendment.id,
                                            'batch': False})
                    start_date = end_period.date_end
                    start_period = end_period.id
        return True
