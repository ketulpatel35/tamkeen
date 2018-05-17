odoo.define('hr_holidays_extension_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .leaves_to_approve': 'action_leaves_to_approve',
    'click .leaves_calendar': 'action_leaves_calendar',
    }, dashboard.prototype.events),
    action_leaves_to_approve: function(event) {
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Requests To Approve"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context: {
                        'default_type': 'remove',
                        'search_default_leave_pending_approval': true,
                        'readonly_by_pass': true
                        },
            domain: [['type','=','remove'],['state','in',['ceo', 'vp',
            'confirm']],'|',['employee_id.leave_manager_id.user_id.id','=',
            user_id],'|',['employee_id.leave_vp_id.user_id.id','=',user_id],
            ['employee_id.leave_ceo_id.user_id.id','=',user_id],],
            search_view_id: self.employee_data.leave_search_view_id,
            target: 'current'
        })
    },
    action_leaves_calendar: function(event) {
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Leaves Calendar"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'calendar,tree,form',
            view_type: 'form',
            views: [[false, 'calendar'],[false, 'list'],[false, 'form']],
            context: {'default_type': 'remove'},
            domain: [['type','=','remove'],],
            search_view_id: self.employee_data.leave_search_view_id,
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
