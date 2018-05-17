# -*- coding:utf-8 -*-
from odoo.addons import decimal_precision as dp
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from dateutil.relativedelta import relativedelta


class contract_init(models.Model):
    _name = 'hr.contract.init'
    _description = 'Initial Contract Settings'

    _inherit = 'ir.needaction_mixin'

    name = fields.Char(string='Name')
    date = fields.Date(string='Effective Date')
    wage_ids = fields.One2many('hr.contract.init.wage',
                               'contract_init_id',
                               string='Starting Wages')
    struct_id = fields.Many2one('hr.payroll.structure',
                                string='Payroll Structure')
    trial_period = fields.Integer(string='Trial Period',
                                  help="Length of Trial Period,"
                                       " in days")
    active = fields.Boolean(string='Active',
                            default=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('approve', 'Approved'),
                              ('decline', 'Declined')],
                             string='State',
                             default='draft')

    # Return records with latest date first
    _order = 'date desc'

    @api.multi
    def unlink(self):
        for record in self:
            if record.state in ['approve', 'decline']:
                raise ValidationError(_('You may not a delete a record '
                                        'that is not in a "Draft" state'))
        return super(contract_init, self).unlink()

    @api.multi
    def set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def state_approve(self):
        for rec in self:
            rec.state = 'approve'

    @api.multi
    def state_decline(self):
        for rec in self:
            rec.state = 'decline'


class init_wage(models.Model):
    _name = 'hr.contract.init.wage'
    _description = 'Starting Wages'

    job_id = fields.Many2one('hr.job', 'Job')

    starting_wage = fields.Float(string='Starting Wage',
                                 digits=dp.get_precision('Payroll'))
    is_default = fields.Boolean(string='Use as Default',
                                help="Use as default wage")
    contract_init_id = fields.Many2one('hr.contract.init',
                                       string='Contract Settings')
    category_ids = fields.Many2many('hr.employee.category',
                                    'contract_init_category_rel',
                                    'contract_init_id',
                                    'category_id', string='Tags')
    _sql_constraints = [('unique_job_cinit',
                         'UNIQUE(job_id, contract_init_id)',
                         _('A Job Position cannot be referenced more'
                           ' than once in a Contract Settings record.')
                         )
                        ]

    @api.multi
    def unlink(self):
        for data in self:
            if data.state in ['approve', 'decline']:
                raise ValidationError(
                    _('You may not a delete a record that is not'
                      ' in a "Draft" state'))
        return super(init_wage, self).unlink()


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    def _get_wage(self, job_id=None):
        res = 0
        default = 0
        init = self.get_latest_initial_values()
        if job_id and job_id.id:
            catdata = job_id
        else:
            catdata = False
        if init:
            for line in init.wage_ids:
                if job_id is not None and line.job_id.id == job_id.id:
                    res = line.starting_wage
                elif catdata:
                    cat_id = False
                    category_ids = [c.id for c in line.category_ids]
                    for ci in catdata.category_ids:
                        if ci.id in category_ids:
                            cat_id = ci.id
                            break
                    if cat_id:
                        res = line.starting_wage
                if line.is_default and default == 0:
                    default = line.starting_wage
                if res != 0:
                    break
        if res == 0:
            res = default
        return res

    def _get_struct(self):
        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.struct_id:
            res = init.struct_id.id
        return res

    def _get_trial_date_start(self):
        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            res = datetime.now().strftime(OE_DFORMAT)
        return res

    def _get_trial_date_end(self):
        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            dEnd = datetime.now().date() + timedelta(days=init.trial_period)
            res = dEnd.strftime(OE_DFORMAT)
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(hr_contract, self).default_get(fields_list)
        # wage = self._get_wage()
        # if wage:
        #     res.update({'wage': wage})
        struct_id = self._get_struct()
        if struct_id:
            res.update({'struct_id': struct_id})
        trial_date_start = self._get_trial_date_start()
        if trial_date_start:
            res.update({'trial_date_start': trial_date_start})
        trial_date_end = self._get_trial_date_end()
        if trial_date_end:
            res.update({'trial_date_end': trial_date_end})
        return res

    # @api.onchange('job_id')
    # def onchange_job(self):
    #     if self.job_id:
    #         wage = self._get_wage(job_id=self.job_id)
    #         self.wage = wage

    @api.onchange('trial_date_start')
    def onchange_trial(self):
        if not self.trial_date_start:
            return None
        trial_date_start = str(self.trial_date_start)
        date_start = datetime.strptime(trial_date_start, "%Y-%m-%d")
        date_end = date_start.date() + relativedelta(months=+3)
        self.trial_date_end = date_end
        init = self.get_latest_initial_values()
        if init is not None and init.trial_period and init.trial_period > 0:
            dStart = datetime.strptime(trial_date_start, OE_DFORMAT)
            dEnd = dStart + timedelta(days=init.trial_period)
            self.trial_date_end = dEnd.strftime(OE_DFORMAT)

    def get_latest_initial_values(self, today_str=None):
        """
        Return a record with an effective date before today_str but
        greater than all others
        :param today_str:
        :return:
        """
        init_obj = self.env['hr.contract.init']
        if today_str is None:
            today_str = datetime.now().strftime(OE_DFORMAT)
        dToday = datetime.strptime(today_str, OE_DFORMAT).date()

        res = None
        init_ids = init_obj.search([('date', '<=', today_str),
                                    ('state', '=', 'approve')])
        for init in init_ids:
            d = datetime.strptime(init.date, OE_DFORMAT).date()
            if d <= dToday:
                if res is None:
                    res = init
                elif d > datetime.strptime(res.date, OE_DFORMAT).date():
                    res = init
        return res
