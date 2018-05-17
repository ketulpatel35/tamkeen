odoo.define('web_js_fix.chat_client_action', function (require) {
"use strict";

require('mail.chat_client_action');
var chat_manager = require('mail.chat_manager');
var core = require('web.core');

core.action_registry.get('mail.chat.instant_messaging').include({
    on_attach_callback: function () {
        chat_manager.bus.trigger('client_action_open', true);
        if (this.channel) {
            this.thread.scroll_to({offset: this.channels_scrolltop[this.channel.id]});
        }
    },
    on_detach_callback: function () {
        chat_manager.bus.trigger('client_action_open', false);
        if(this.channel){
	        this.channels_scrolltop[this.channel.id] = this.thread.get_scrolltop();
	    }
    },
    destroy: function() {
        if (this.$buttons){
            this.$buttons.off().destroy();
            this._super.apply(this, arguments);
        }
    },
});

});