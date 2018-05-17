# -*- coding:utf-8 -*-
from odoo import api, fields, models


class PolicyGroups(models.Model):
    _name = 'hr.policy.group'
    _description = 'HR Policy Groups'

    name = fields.Char('Name')
    contract_ids = fields.One2many('hr.contract', 'policy_group_id',
                                   string='Contracts')


class ContractInit(models.Model):
    _inherit = 'hr.contract.init'

    policy_group_id = fields.Many2one('hr.policy.group',
                                      string='Policy Group')


class HrContract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    policy_group_id = fields.Many2one('hr.policy.group',
                                      string='Policy Group')

    def _get_policy_group(self):
        """
        set default policy group.
        -------------------------
        :param cr:
        :param uid:
        :param context:
        :return:
        """
        res = False
        init = self.get_latest_initial_values()
        if init is not None and init.policy_group_id:
            res = init.policy_group_id.id
        return res

    # _defaults = {
    #     'policy_group_id': _get_policy_group,
    # }

    @api.model
    def default_get(self, fields_list):
        res = super(HrContract, self).default_get(fields_list)
        policy_group_id = self._get_policy_group()
        if policy_group_id:
            res.update({'policy_group_id': policy_group_id})
        return res
