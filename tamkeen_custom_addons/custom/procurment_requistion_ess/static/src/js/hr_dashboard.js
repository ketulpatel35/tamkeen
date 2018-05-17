odoo.define('procurment_requistion_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .procurement_requisition_to_approve':
            'action_procurement_requisition_to_approve',
    }, dashboard.prototype.events),
    action_procurement_requisition_to_approve: function(event) {
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Procurement Requisition to Approve"),
            type: 'ir.actions.act_window',
            res_model: 'purchase.requisition',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context: {
                        'search_default_group_state':1,
                        'search_default_mngr_pr_to_approve':1
                        },
            domain: [['state','in',['ceo', 'tomanager_app', 'vp']]],
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
