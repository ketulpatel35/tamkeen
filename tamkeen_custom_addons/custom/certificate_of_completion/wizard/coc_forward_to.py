from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime


class COCForwardTo(models.TransientModel):
    _name = 'coc.forward.to.wiz'

    STATE_FORWARD = [
        ('draft', 'To Submit'),
        ('business_owner_approval', 'Business Owner Approval'),
        ('pmo_approval', 'PMO Approval'),
        ('finance_processing', 'Finance Processing'),
        ('rejected', 'Rejected')]

    def get_forward_state(self):
        """
        get state
        :return:
        """
        state = []
        if self._context and self._context.get('first_approval'):
            state = [('draft', 'Draft'),
                     ('business_owner_approval', 'Business Owner Approval'),
                     ('finance_processing', 'Finance Processing'),
                     ('rejected', 'Rejected')]
        elif self._context and self._context.get('second_approval'):
            state = [('draft', 'Draft'),
                     ('pmo_approval', 'PMO Approval'),
                     ('finance_processing', 'Finance Processing'),
                     ('rejected', 'Rejected')]
        return state

    state = fields.Selection(get_forward_state)
    business_owner = fields.Many2one('res.users', 'Business Owner')
    reason = fields.Char('Reason')

    def get_business_owner_user(self):
        """

        :return:
        """
        usr_list = []
        for rec in self.env['res.users'].search([]):
            if rec.has_group('certificate_of_completion.'
                             'group_coc_business_owner_approval'):
                usr_list.append(rec.id)
        return usr_list

    @api.onchange('state')
    def onchange_state(self):
        """
        onchange state
        :return:
        """
        res = {}
        business_owner_user = []
        if self.state == 'business_owner_approval':
            business_owner_user = self.get_business_owner_user()
        res.update({'business_owner': [('id', 'in', business_owner_user)]})
        return {'domain': res}

    @api.multi
    def coc_forward_to(self):
        """
        COC forward to next
        :return:
        """
        res_rec = False
        if self._context and self._context.get('res_id'):
            res_rec = self.env['certificate.of.completion'].browse(
                self._context.get('res_id'))
        if res_rec:
            if self.state == 'draft':
                self.env['service.log'].create({
                    'state_from': res_rec.state,
                    'state_to': 'Returned',
                    'user_id': self._context.get('uid'),
                    'reason': self.reason,
                    'activity_datetime': datetime.now().strftime(OE_DTFORMAT),
                    'coc_request_id': res_rec.id})
                # set to draft record
                res_rec.coc_service_validate10()
                return True
            elif self.state == 'rejected':
                self.env['service.log'].create({
                    'state_from': res_rec.state,
                    'state_to': 'Rejected',
                    'user_id': self._context.get('uid'),
                    'reason': self.reason,
                    'activity_datetime': datetime.now().strftime(OE_DTFORMAT),
                    'coc_request_id': res_rec.id})
                res_rec.coc_service_validate6()
            elif self.state == 'business_owner_approval':
                res_rec.business_owner = self.business_owner.id
                res_rec.coc_service_validate7()
            elif self.state == 'pmo_approval':
                res_rec.coc_service_validate9()
            elif self.state == 'finance_processing':
                res_rec.coc_service_validate11()