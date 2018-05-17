from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import odoo.addons.decimal_precision as dp
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT


class wage_increment(models.Model):
    _name = 'hr.contract.wage.increment'
    _description = 'HR Contract Wage Adjustment'

    _rec_name = 'effective_date'

    @api.model
    def default_get(self, fields):
        res = super(wage_increment, self).default_get(fields)
        if self._context and self._context.get('active_model') \
                and self._context.get('active_model') == 'hr.employee':
            if res and not res.get('contract_id'):
                raise Warning(_('You can not Wage Adjustment without '
                                'Contract!'))
        return res

    @api.multi
    def _calculate_difference(self):
        for incr in self:
            if incr.wage >= incr.contract_id.wage:
                if incr.contract_id.wage == 0:
                    percent = 0
                else:
                    percent = \
                        ((incr.wage / incr.contract_id.wage) - 1.0) * 100.0
            else:
                if incr.contract_id.wage == 0:
                    percent = 0
                else:
                    percent = (1.0 - (incr.wage / incr.contract_id.wage)
                               ) * -100.0
            incr.wage_difference = incr.wage - incr.c_wage
            incr.wage_difference_percent = percent

    @api.model
    def _get_contract_data(self):
        employee_id = self._get_employee()
        ee_data = self.env['hr.employee'].browse(employee_id)
        if self._context.get('active_model') == 'hr.employee':
            return ee_data.contract_id.id or False
        hr_contract_obj = self.env['hr.contract']
        hr_contract_rec = hr_contract_obj.search([
            ('employee_id', '=', ee_data.id), ('is_active', '=', True)])
        if not hr_contract_rec:
            contract_id = ee_data.contract_id or False
        # This code is commented for the migration
        else:
            #     if len(hr_contract_rec) > 1:
            #         raise Warning(_('Multiple
            #  Active Contract fount for Employee '
            #                         ': %s') % (ee_data.name))
            contract_id = hr_contract_rec[0]
        if not contract_id:
            return False
        return contract_id.id

    @api.model
    def _get_employee(self):
        employee_id = self._context.get('active_id', False)
        return employee_id

    @api.model
    def _get_effective_date(self):
        """
        :return:
        """
        if not self.contract_id:
            return False

        contract = self.contract_id
        # if contract.pps_id:
        first_day = 1
            # if contract.pps_id.type == 'monthly':
            #     first_day = contract.pps_id.mo_firstday
        dThisMonth = datetime.strptime(datetime.now().strftime(
            '%Y-%m-' + first_day), DEFAULT_SERVER_DATE_FORMAT).date()
        dNextMonth = datetime.strptime(
            (datetime.now() +
             relativedelta(
                 months=+
                 1)).strftime(
                '%Y-%m-' +
                first_day),
            DEFAULT_SERVER_DATE_FORMAT).date()
        if dThisMonth < datetime.now().date():
            return dNextMonth.strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            return dThisMonth.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return False

    effective_date = fields.Date(string='Effective Date',
                                 default=_get_effective_date)
    wage = fields.Float(
        'New Wage',
        digits=dp.get_precision('Payroll'))
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        default=_get_contract_data, store=True)
    c_wage = fields.Float(string='Current Wage', related='contract_id.wage')
    wage_difference = fields.Float(
        compute="_calculate_difference",
        string='Difference',
        multi='diff')
    wage_difference_percent = fields.Float(
        compute="_calculate_difference",
        type='float',
        string='Percentage',
        multi='diff')
    employee_id = fields.Many2one('hr.employee',
                                  related='contract_id.employee_id',
                                  string='Employee',
                                  store=True,
                                  default=_get_employee)
    job_id = fields.Many2one('hr.job', related='contract_id.job_id',
                             string='Job', store=True)
    department_id = fields.Many2one(
        relation='hr.department',
        related='employee_id.department_id',
        string='Organization Unit',
        store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('decline', 'Declined')
    ], 'State', default='draft')

    run_id = fields.Many2one(
        'hr.contract.wage.increment.run',
        string='Batch Run',
        ondelete='cascade',
        copy=True)

    @api.model
    def _check_state(self, wage_incr):
        """
        :param wage_incr:
        :return:
        """
        if not wage_incr.contract_id:
            raise Warning(_('Invalid Contract for Employee : %s'
                            ) % (wage_incr.employee_id.name))
        wage_incr_ids = self.search([
            ('contract_id', '=', wage_incr.contract_id.id),
            ('state', 'in', ['draft', 'confirm', 'approved']),
            ('id', '!=', wage_incr.id)])
        name = wage_incr.contract_id.name
        if len(wage_incr_ids) > 0:
            raise Warning(_('Warning \n '
                            'There is already another wage adustment in '
                            'progress for this contract: %s.') % (name))
        if wage_incr.contract_id.state in ['draft', 'done']:
            name = wage_incr.contract_id.name
            raise Warning(_('Warning! \n The current state of the contract '
                            'does not permit a wage change: %s') % (name))
        if wage_incr.contract_id.date_end:
            dContractEnd = datetime.strptime(wage_incr.contract_id.date_end,
                                             DEFAULT_SERVER_DATE_FORMAT)
            dEffective = datetime.strptime(wage_incr.effective_date,
                                           DEFAULT_SERVER_DATE_FORMAT)
            if dEffective >= dContractEnd:
                name = wage_incr.contract_id.name
                raise Warning(_('Warning! \n The contract end date is on or '
                                'before the effective date of the adjustment:'
                                ' %s') % (name))
        return True

    @api.multi
    def action_wage_increment(self):
        hr_contract_obj = self.env['hr.contract']
        # Copy the contract and adjust start/end dates and wage accordingly.
        for wage_inc_rec in self:
            if wage_inc_rec.wage_difference > -0.01 \
                    and wage_inc_rec.wage_difference < 0.01:
                continue
            self._check_state(wage_inc_rec)
            default = {
                # 'wage': wage_inc_rec.wage,
                'date_start': wage_inc_rec.effective_date,
                'name': False,
                'state': 'open',
                'message_ids': False,
                'trial_date_start': False,
                'trial_date_end': False,
                'is_active': True,
            }
            data = wage_inc_rec.contract_id.copy_data(default=default)[0]
            notes = data.get('notes', False)
            if not notes:
                notes = ''
            notes = notes + '\nSupercedes (because of' \
                            ' wage adjustment) previous' \
                            ' contract: ' + wage_inc_rec.contract_id.name
            data['notes'] = notes
            data['name'] = "Auto Adjustment - " + str(
                wage_inc_rec.contract_id.id)
            new_contract_rec = hr_contract_obj.with_context({
                'cr_seq': wage_inc_rec.contract_id.name}).create(data)
            # update wage inc history
            new_contract_rec.wage_inc_history_ids = [
                (4, wage_inc_rec.contract_id.id)]
            new_contract_rec.write({'wage': wage_inc_rec.wage})
            if new_contract_rec:
                if wage_inc_rec.contract_id.notes:
                    notes = wage_inc_rec.contract_id.notes
                else:
                    notes = ''
                notes = notes + '\nSuperceded (for wage adjustment) by ' \
                                'contract: ' + wage_inc_rec.contract_id.name
                # Set the new contract to the appropriate state
                new_contract_rec.signal_confirm_all()
                # Terminate the current contract (and trigger appropriate state
                # change)
                end_date = datetime.strptime(
                    wage_inc_rec.effective_date,
                    OE_DFORMAT).date() + relativedelta(days=-1)
                vals = {'notes': notes,
                        'from_amend': 'Wage Adjustment',
                        'date_end': end_date,
                        'is_active': False
                        }
                wage_inc_rec.contract_id.write(vals)
                wage_inc_rec.contract_id.state_amendment()
        return

    @api.model
    def create(self, vals):
        contract_id = vals.get('contract_id', False)
        contract_pool = self.env['hr.contract']
        # when record create from employee action(wizard)
        cont_rec = False
        if self._context.get(
                'active_model') == 'hr.employee':
            employee_rec = self.env['hr.employee'].browse(
                self._context.get('active_id'))
            cont_rec = employee_rec.contract_id
            # cont_rec =
            # cont_rec = contract_pool.search(
            #     [('employee_id', '=', self._context.get('active_id')),
            #      ('is_active', '=', True)])
            # Comment for Migration
            # if cont_rec and len(cont_rec) > 1:
            #     raise Warning(_('multiple
            #  contract found for this employee '))
            # if not contract_id:
            #     contract_id = cont_rec.id
        # record create from batch
        if self._context.get(
                'active_model') == 'hr.contract.wage.increment.run':
            if not contract_id and self._context is not None:
                contract_id = self._context.get('active_id')
            cont_rec = contract_pool.browse(contract_id)

        if cont_rec:
            for cont in cont_rec:
                if vals.get('effective_date') <= cont.date_start:
                    raise Warning(_('The effective date of the adjustment'
                                    ' must be after the contract'
                                    ' start date. Contract:'
                                    ' %s.') % (cont.name))
            wage_incr_ids = self.search([
                ('contract_id', '=', cont_rec.id),
                ('state', 'in', ['draft', 'confirm', 'approved'])])
            if len(wage_incr_ids) > 0:
                raise Warning(_('There is already another wage adustment in '
                                'progress for this contract: %s.') % (
                              cont_rec.name))
        return super(wage_increment, self).create(vals)

    @api.multi
    def do_signal_confirm(self):
        for rec in self:
            self._check_state(rec)
            rec.write({'state': 'confirm'})

    @api.multi
    def do_signal_approve(self):
        for rec in self:
            rec.action_wage_increment()
            rec.write({'state': 'approve'})

    @api.multi
    def unlink(self):
        for incr in self:
            if incr.state in ['approve']:
                raise Warning(_('The record cannot be deleted! You may not \
                    delete a record that is in a %s state:\nEmployee: %s') % (
                    incr.state, incr.employee_id.name))

        return super(wage_increment, self).unlink()

    @api.multi
    def do_signal_decline(self):
        """
        :return:
        """
        for rec in self:
            rec.state = 'decline'


class wage_increment_run(models.Model):
    _name = 'hr.contract.wage.increment.run'
    _description = 'Wage Increment Batches'

    _inherit = ['ir.needaction_mixin']

    name = fields.Char('Name')
    effective_date = fields.Date(string='Effective Date')
    type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percent', 'Percentage'),
        ('final', 'Final Amount'),
        ('manual', 'Manual'),
    ], string='Type')
    adjustment_amount = fields.Float(
        string='Adjustment Amount',
        digits=dp.get_precision('Payroll'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('decline', 'Declined')
    ], 'State', default='draft')
    increment_ids = fields.One2many(
        'hr.contract.wage.increment',
        'run_id',
        string='Adjustments',
        copy=True)

    @api.model
    def _needaction_domain_get(self):

        users_obj = self.env['res.users']

        if users_obj.has_group('hr_admin.group_hr_admin'):
            domain = [('state', 'in', ['confirm'])]
            return domain

        return False

    @api.multi
    def unlink(self):
        for run in self:
            if run.state in ['approve']:
                raise \
                    Warning(_('The adjustment run cannot be'
                              ' deleted! You may not delete'
                              ' a wage adjustment that is'
                              ' in the %s state.') % (run.state))

        return super(wage_increment_run, self).unlink()

    @api.multi
    def state_confirm(self):
        for rec_inc_run in self:
            for rec_inc in rec_inc_run.increment_ids:
                rec_inc.do_signal_confirm()
            rec_inc_run.state = 'confirm'

    @api.multi
    def state_approve(self):
        for rec_inc_run in self:
            for rec_inc in rec_inc_run.increment_ids:
                rec_inc.do_signal_approve()
            rec_inc_run.state = 'approve'

    @api.multi
    def state_decline(self):
        for rec_inc_run in self:
            for rec_inc in rec_inc_run.increment_ids:
                rec_inc.state = 'decline'
            rec_inc_run.state = 'decline'


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    wage_inc_history_ids = fields.Many2many('hr.contract',
                                            'hr_contract_history',
                                            'new_c_id', 'old_c_id',
                                            string='Wage Increment History')
    is_active = fields.Boolean('is Active', default=True)
    from_amend = fields.Char(string='From Amendment')

    @api.multi
    def state_renew(self):
        res = super(hr_contract, self).state_renew()
        for rec in self:
            rec.wage_inc_history_ids = False
            res.update({'is_active': False})
        return res

    @api.multi
    def state_pending_done(self):
        wi_ids = False
        for i in self:
            wi_ids = self.env['hr.contract.wage.increment'].search([
                ('contract_id', '=', i.id),
                ('state', 'in', [
                    'draft', 'confirm']),
            ], )
        if wi_ids:
            # data = self.env['hr.contract'].read(i, ['name'])
            raise Warning(
                _('There is a wage adustment in progress for this contract. '
                  'Either delete the adjustment or delay the termination of '
                  'contract.'))
        return super(hr_contract, self).state_pending_done()


class hr_emp_count(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _wage_count(self):
        Contract = self.env['hr.contract.wage.increment']
        for rec in self:
            no_of_emp = Contract.search_count([('employee_id', '=', rec.id)])
            rec.wage_count = no_of_emp

    wage_count = fields.Integer(compute="_wage_count", string='Wage')

    @api.multi
    def signal_confirm(self):
        hr_contract_obj = self.env['hr.contract']
        for rec in self:
            releted_contract = hr_contract_obj.\
                search([('employee_id', '=', rec.id),
                        ('is_active', '=', True)])
            if not releted_contract:
                raise Warning(_('you can not confirm employee without a '
                                'contract!'))
            rec.write({'status': 'onboarding'})

    def _compute_contracts_count(self):
        """
        add domain for count is_active record.
        :return:
        """
        contract_data = self.env['hr.contract'].sudo().read_group([
            ('employee_id', 'in', self.ids), ('is_active', '=', True)],
            ['employee_id'], ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count'])
                      for data in contract_data)
        for employee in self:
            employee.contracts_count = result.get(employee.id, 0)
