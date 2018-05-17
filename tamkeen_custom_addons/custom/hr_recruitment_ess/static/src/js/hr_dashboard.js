odoo.define('hr_recruitment_ess.dashboard', function (require) {
"use strict";
var core = require('web.core');
var session = require('web.session');
var dashboard = require('hr_dashboard.dashboard');

var _t = core._t;
var _lt = core._lt;

dashboard.include({
    events: _.extend({
    'click .positions_vacant': 'action_positions_vacant',
    'click .positions_occupied': 'action_positions_occupied',
    }, dashboard.prototype.events),
    action_positions_vacant: function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Vacant Positions"),
            type: 'ir.actions.act_window',
            res_model: 'hr.job',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context: {},
            domain: [['employee_id', '=', false], ['vacant','=',true]],
            target: 'current'
        })
    },
    action_positions_occupied: function(event){
        var self = this;
        var user_id = session.uid;
        event.stopPropagation();
        event.preventDefault();
        this.do_action({
            name: _t("Occupied Positions"),
            type: 'ir.actions.act_window',
            res_model: 'hr.job',
            view_mode: 'tree,form',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            context: {},
            domain: [['employee_id', '!=', false],
            ['employee_id.user_id.id', '=', user_id],
            ['employee_id.parent_id.user_id.id', '=', user_id]],
            target: 'current'
        })
    },
})
// View adding to the registry
//core.view_registry.add('hr_dashboard_view', HrDashboardView);
//return HrDashboardView
});
