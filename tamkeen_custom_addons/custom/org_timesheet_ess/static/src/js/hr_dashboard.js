odoo.define('org_timesheet_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .timesheets_to_approve': 'action_timesheets_to_approve',
    }, dashboard.prototype.events),
    action_timesheets_to_approve: function(event) {
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Timesheets to Approve"),
            type: 'ir.actions.act_window',
            res_model: 'hr_timesheet_sheet.sheet',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context: {
                        'search_default_loan_pending_approval': true,
                        'readonly_by_pass': true,
                    },
            domain: ['|',['employee_id.timesheet_manager_id.user_id.id','=',
             user_id],'|',['employee_id.timesheet_vp_id.user_id.id','=',
             user_id], ['employee_id.timesheet_ceo_id.user_id.id','=',
             user_id], ],
            search_view_id: self.employee_data.timesheet_search_view_id,
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
