odoo.define('org_performance_appraisal_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .performance_appraisal_request_to_approve':
        'action_performance_appraisal_request_to_approve',
    }, dashboard.prototype.events),
    action_performance_appraisal_request_to_approve: function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Appraisal Performance Request To Approve"),
            type: 'ir.actions.act_window',
            res_model: 'performance.appraisal',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'], [false, 'form']],
            context: {
                        'search_default_pa_pending_approval': true,
                        'readonly_by_pass': true
                        },
            domain: ['|', ['employee_id.pa_manager_id.user_id.id', '=',
            user_id], '|', ['employee_id.pa_vp_id.user_id.id', '=', user_id],
            ['employee_id.pa_ceo_id.user_id.id', '=', user_id]],
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
