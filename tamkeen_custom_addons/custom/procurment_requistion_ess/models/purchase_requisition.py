from odoo import fields, models, api, _


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    @api.multi
    def _get_related_window_action_id(self, data_pool, dest_state,
                                      service_provider):
        window_action_id = window_action_ref = False
        if service_provider == 'purchase_requisition':
            window_action_ref = \
                'purchase_requisition.action_purchase_requisition'
            if dest_state == 'tomanager_app':
                window_action_ref = \
                    'procurment_requistion_ess.purchase_action_for_pr_employee'
            elif dest_state in ['vp', 'ceo']:
                window_action_ref = \
                    'procurment_requistion_ess.purchase_budget_all_emp_action'
            elif dest_state == 'budget':
                window_action_ref = 'procurment_requistion_ess.action_' \
                                    'purchase_requisition_for_budget_approval'
            elif dest_state == 'procurement_review':
                window_action_ref = 'procurment_requistion_ess.' \
                                    'action_purchase_requisition_for_' \
                                    'procurement_review'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id