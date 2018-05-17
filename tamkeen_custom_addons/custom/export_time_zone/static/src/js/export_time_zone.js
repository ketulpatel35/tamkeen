odoo.define('export_time_zone.export_time_zone', function (require) {
'use strict';

var DataExport = require('web.DataExport');
var Model = require('web.Model');
var session = require('web.session');

DataExport.include({
    events: _.extend({
    'click .o_export_with_timezone':  'export_time_zone_input',
    'change #time_zone_selector': 'on_change_time_zone_selector',
    }, DataExport.prototype.events),

    export_time_zone_input: function () {
        var export_with_timezone = $('.o_export_with_timezone')
        var select_time_zone = $('.o_select_time_zone')
        var time_zone_selector = $('select#time_zone_selector');
        var utc_err_msg = $('.o_utc_err_msg');
        utc_err_msg.hide();
        if(export_with_timezone.prop("checked") == true){
            var tz = new Model('res.company').call("tz_get", [[]]).then(function(result){
                var result_len = result.length
                var options = "";
                var user_context = session.user_context
                for (var i=0;i<result_len;i++)
                    {
                        if (user_context['tz'] == result[i][0]){
                            options += "<option selected='selected' value='"+ result[i][0] +"'>"+result[i][1]+"</option>"
                            session.user_context.selected_tz = result[i][0]
                            if (user_context['tz'] != 'UTC'){
                                utc_err_msg.show()
                            }
                        }
                        else{
                            options += "<option value='"+ result[i][0] +"'>"+result[i][1]+"</option>"
                        }
                    }
                time_zone_selector.html(options);
            });
            select_time_zone.css('display','block');
        }
        else {
            select_time_zone.css('display','none');
            session.user_context.selected_tz = 'UTC'
        }
    },

    on_change_time_zone_selector: function() {
        var time_zone_selector_value = $('select#time_zone_selector').val();
        session.user_context.selected_tz = time_zone_selector_value
        var utc_err_msg = $('.o_utc_err_msg');
        utc_err_msg.hide();
        if (time_zone_selector_value != 'UTC'){
            utc_err_msg.show();
        }
    },
    });
});