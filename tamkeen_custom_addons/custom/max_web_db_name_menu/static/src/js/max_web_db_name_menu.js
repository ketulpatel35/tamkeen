odoo.define('max_web_db_name_menu.max_web_db_name_menu', function (require) {
'use strict';

    var session = require('web.session');
    var UserMenu = require('web.UserMenu');

    UserMenu.include({
        do_update: function () {
            var self = this;
            this._super.apply(this, arguments);

            if(session.debug)
                return;
            else {
                var topbar_name = self.$el.find('.oe_topbar_name').text();
                topbar_name = _.str.sprintf("%s (%s)", topbar_name, session.db);
                self.$el.find('.oe_topbar_name').text(topbar_name);
            }
        },
    });
});
