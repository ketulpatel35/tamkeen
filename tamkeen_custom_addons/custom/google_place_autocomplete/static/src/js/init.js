/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('google_place_autocomplete.init', function (require) {
    "use strict";
    var Model = require('web.Model');
    //default key
    var default_key = 'AIzaSyAu47j0jBPU_4FmzkjA3xc_EKoOISrAJpI';

    new Model('gmap.config').call('get_key_api', []).then(function (key) {
        if (!key) {
            key = default_key;
        }
        $.getScript('http://maps.googleapis.com/maps/api/js?key=' + key + '&libraries=places');
    });
});