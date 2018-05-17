odoo.define('bista_spagobi_sso', function (require) {
"use strict";


var core = require('web.core');
var Widget = require('web.Widget');
var Model = require('web.Model');

var SpagoBI_App = Widget.extend({
    template: 'SpagoBI_App_Template',

    init: function(parent){
    	var self = this;
        this.parent = parent;
        self.spagobi_login();
        return this._super.apply(this, arguments);
    },

    spagobi_login: function(){
        var self = this;
        this.rpc('/bista_spagobi_sso/spagobi_login', {}).then(function (result) {
            var csession = result.cookies_session;
            var cname = "JSESSIONID";
            var cvalue = csession;
            var subdomain = result.subdomain;
            self.auto_login();
            self.setCookie(subdomain,cname,cvalue);
        });
    },

    auto_login:function(){
        var self = this;
        this.rpc('/bista_spagobi_sso/spagobi_login_url', {}).then(function (result) {
            var third_conf = result;
            var height = jQuery(".oe_application, .o_content").height() + 60;
            jQuery('#spagobi_app_id').css({"width":"100%","height":height + "px"});
            jQuery(".oe_leftbar").hide();
            var d = third_conf.url;
            if (!third_conf.url) alert("Please check SpagoBI Web Application URL configuration or contact to you administartor.\n(Might be configuration URL is not set.)");
            jQuery('#spagobi_app_id').attr('src', d);
        });
    },

    setCookie: function(subdomain, cname, cvalue) {
        document.cookie = cname + " = " + cvalue + ";domain="+subdomain+";expires=session;path=/SpagoBI/";
    },

});

core.action_registry.add('spagobi_app.main', SpagoBI_App);

return SpagoBI_App;

});
