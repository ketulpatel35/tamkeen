odoo.define('hr_overtime_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .overtime_pre_requests_to_approve':
            'action_overtime_pre_requests_to_approve',
    'click .overtime_claims_to_approve': 'action_overtime_claims_to_approve',
    }, dashboard.prototype.events),
    action_overtime_pre_requests_to_approve : function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Pre-Approval Request To Approve"),
            type: 'ir.actions.act_window',
            res_model: 'overtime.pre.request',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'], [false, 'form']],
            context:{
                        'search_default_pending_approval':1
                        },
            domain: ['|', ['employee_id.overtime_manager_id.user_id.id', '=',
            user_id], '|', ['employee_id.overtime_vp_id.user_id.id', '=',
            user_id], ['employee_id.overtime_ceo_id.user_id.id', '=',
            user_id]],
            target: 'current'
        })
    },
    action_overtime_claims_to_approve : function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Claim Request To Approve"),
            type: 'ir.actions.act_window',
            res_model: 'overtime.statement.request',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'], [false, 'form']],
            context: {'search_default_pending_approval': true},
            domain: ['|', ['employee_id.overtime_manager_id.user_id.id', '=',
            user_id], '|', ['employee_id.overtime_vp_id.user_id.id', '=',
            user_id], ['employee_id.overtime_ceo_id.user_id.id', '=',
            user_id]],
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
