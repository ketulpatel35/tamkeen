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

function openerp_chart(instance) {

    var module = instance.organization_chart;
    var _t     = instance.web._t;
    var QWeb   = instance.web.qweb;
    
    instance.web.WebClient = instance.web.WebClient.extend({
        init: function(parent, params){
            this._super(parent,params);
            var self = this;
        },

        start: function(){
            window.document.title = 'Organization Structure';   
            this._super();
            var self = this;
            this.title="Organization Structure";
            $('.js_pick_quit').click(function(){ 
              return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'open_view_employee_list_my']], ['res_id']).pipe(function(res) {
                window.location = '/web#action=' + res[0]['res_id'];
              }); 
            });
            var deferred_promises = [];  
            return $.when.apply($, deferred_promises).then(function(){
              stopsplash(100);
              self.$(".oe_loading").hide();
              self.draw_tree_structure();
            });
        },

        draw_tree_structure: function(){
            startsplash();
            self.model_tree_chart = new instance.web.Model("tree.chart.config");
            self.model_tree_chart.call("draw_tree_structure", [[]]).then(function(result){  
                  draw_tree_structure = result['rec_tree_data'];
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
}

openerp.organization_chart = function(instance) {
    var _t = instance.web._t;
    instance.organization_chart = instance.organization_chart || {};
    openerp_chart(instance);
}