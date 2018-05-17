odoo.define('hr_payroll_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .employee_payslip': 'action_employee_payslip',
    }, dashboard.prototype.events),
    action_employee_payslip : function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Employee Payslip"),
            type: 'ir.actions.act_window',
            res_model: 'hr.payslip',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'], [false, 'form']],
            context: {},
            domain: [['employee_id.user_id.id', '=', user_id],
            ['employee_id.parent_id.user_id.id','=', user_id]],
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
