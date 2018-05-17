odoo.define('web_track_delete.web_track_delete', function (require) {
"use strict";
    var core = require('web.core');
    var _t = core._t;
    var Sidebar = require('web.Sidebar');
    var Model = require('web.Model');
    var session = require('web.session');
    var user_id = false;

    Sidebar.include({
        add_items: function(section_code, items) {
            var self = this;
            var user_id = -1;

            $.ajaxSetup({async:false});
            var allowed_user_id = new Model('track.delete').call("can_delete", [[]]).then(function(result){
                user_id = result;
            });
            $.ajaxSetup({async:true});

            if (this.session.uid == user_id) {
                this._super.apply(this, arguments);
            }
            else {
                var delete_label = _t('Delete');
                var new_items = items;
                if (section_code == 'other') {
                    new_items = [];
                    for (var i = 0; i < items.length; i++) {
                        if (items[i]['label'] != delete_label) {
                            new_items.push(items[i]);
                        };
                    };
                };
                if (new_items.length > 0) {
                    this._super.call(this, section_code, new_items);
                };
            }
        },
    });
});
