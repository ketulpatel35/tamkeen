from odoo import fields, models, api, _


class BusinessTripAllowance(models.Model):
    _name = 'business.trip.allowance'
    _description = 'Business Trip Items'
    _order = 'name desc'

    name = fields.Char('Name')
    code = fields.Char('Code')
    account_id = fields.Many2one('account.account',
                                 string='Account', copy=False)
    description = fields.Text('Description')


class BTAllowanceCalculation(models.Model):
    _name = 'bt.allowance.cal'
    _description = 'Business Trip Calculation'

    bt_allowance_id = fields.Many2one('business.trip.allowance',
                                      'Item')
    per_day_amount = fields.Float('Per Day Amount')
    amount = fields.Float('Total Trip Cost')
    remarks = fields.Text('Remarks')
    business_trip_id = fields.Many2one('org.business.trip', 'Business Trip')
    account_id = fields.Many2one('account.account', 'Account')

    @api.onchange('bt_allowance_id')
    def onchange_bt_allowance(self):
        """
        Onchange Allowance
        :return:
        """
        if self.bt_allowance_id and self.bt_allowance_id.account_id:
            self.account_id = self.bt_allowance_id.account_id.id