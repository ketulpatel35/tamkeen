function startsplash(){
    stopsplash();
    $('#dvLoading').show();
    setTimeout(stopsplash,3000000);
}
function stopsplash(secs){
     $('#dvLoading').fadeOut(secs);
}

function get_orientation(getOrgChart,key){
  switch(key) {
    case 'RO_BOTTOM':
        return getOrgChart.RO_BOTTOM
        break;
    case 'RO_RIGHT':
        return getOrgChart.RO_RIGHT
        break;
    case 'RO_LEFT':
        return getOrgChart.RO_LEFT
        break;
    case 'RO_TOP_PARENT_LEFT':
        return getOrgChart.RO_TOP_PARENT_LEFT
        break;
    case 'RO_BOTTOM_PARENT_LEFT':
        return getOrgChart.RO_BOTTOM_PARENT_LEFT
        break;
    case 'RO_RIGHT_PARENT_TOP':
        return getOrgChart.RO_RIGHT_PARENT_TOP
        break;
    case 'RO_LEFT_PARENT_TOP':
        return getOrgChart.RO_LEFT_PARENT_TOP
        break;
    default:
        return getOrgChart.RO_TOP
  } 
}

odoo.define('organization_chart.treeChart', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.DataModel');
// var Session = require('web.Session');
var WebClient = require('web.WebClient');

var QWeb = core.qweb;
var _t = core._t;

var TreeChart = WebClient.extend({
    init: function(parent){
        var self = this;
        this._super(arguments[0],{});
        this.started = new $.Deferred(); // resolves when DOM is online
        this.ready = new $.Deferred(); // resolves when the whole GUI has been loaded
    },

    start: function(){
        window.document.title = 'Organization Structure';
        var self = this;
        this.title="Organization Structure";
        $('.js_pick_quit').click(function(){ 
          return new Model('ir.model.data').call('search_read', [['name', '=', 'open_view_employee_list_my']], ['res_id']).pipe(function(res) {
            window.location = '/web#action=' + res[0]['res_id'];
          });
        });
        

        var deferred_promises = [];  
        return $.when.apply($, deferred_promises).then(function(){
          stopsplash(337);
          self.$(".oe_loading").hide();
          self.draw_tree_structure();
        });
    },

    draw_tree_structure: function(){
        startsplash();
        console.log('TREEEEEEEE', $('#tree_id').text())
        var tree_id = $('#tree_id').text();
        self.model_tree_chart = new Model('tree.chart.config');
        self.model_tree_chart.call('draw_tree_structure', [[tree_id]]).then(function(result){  
              self.draw_tree_structure = result['rec_tree_data'];
              var peopleElement = document.getElementById("org_structure");
              var orgChart = new getOrgChart(peopleElement, {
                  // idField: 'id',//result['idField'],//"Key",
                  // parentIdField: 'parentId',//result['parentIdField'],
                  primaryFields: result['primaryFields'],
                  photoFields: result["photoFields"],
                  enableEdit: result['enableEdit'],
                  enableZoom: result['enableZoom'],
                  enableSearch: result['enableSearch'],
                  enableGridView: result['enableGridView'],
                  linkType: result['linkType'].toUpperCase(),
                  orientation: get_orientation(getOrgChart,result['orientation']),
                  enableDetailsView: result['enableDetailsView'],
                  enablePrint: result['enablePrint'],
                  theme: result['theme_type'],
                  color: result['color'],
                  expandToLevel: result['expandToLevel'],
                  dataSource: draw_tree_structure  
              });
              $('#dept_count').text(result['dept_count']);  
              stopsplash(500);
        });     
    },

});

return {
    TreeChart: TreeChart,
};
});


odoo.define('organization_chart.main', function (require) {
"use strict";

var treeChart = require('organization_chart.treeChart');
var core = require('web.core');

core.action_registry.add('act_organization_chart_tag', treeChart.TreeChart);

});
