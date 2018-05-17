odoo.define('service_management_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .general_services_requests_to_approve':
            'action_general_services_requests_to_approve',
    }, dashboard.prototype.events),
    action_general_services_requests_to_approve: function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("General Services Requests to Approve"),
            type: 'ir.actions.act_window',
            res_model: 'service.request',
            view_mode: 'kanban,tree,form',
            view_type: 'form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            context: {
                        'search_default_pending_approvals': true,
                        'default_service_provider': 'hr'
                        },
            domain: ['|', ['employee_id.service_manager_id.user_id.id', '=',
            user_id], '|', ['employee_id.service_vp_id.user_id.id', '=',
            user_id], ['employee_id.service_ceo_id.user_id.id', '=',user_id],],
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
