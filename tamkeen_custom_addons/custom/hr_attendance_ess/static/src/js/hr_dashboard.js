odoo.define('hr_attendance_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .attendance_change_req_to_approved':
            'action_attendance_change_req_to_approved',
    }, dashboard.prototype.events),
    action_attendance_change_req_to_approved: function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Attendances"),
            type: 'ir.actions.act_window',
            res_model: 'attendance.change.request',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context:{
                        'search_default_group_name': true,
                        'search_default_mngr_pr_to_approve': true,
                    },
            domain: [['state', 'in', ['for_review']],
            ['employee_id.attendance_manager_id.user_id.id', '=', user_id]],
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
