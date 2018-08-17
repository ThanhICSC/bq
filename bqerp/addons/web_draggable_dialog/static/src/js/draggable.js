//-*- coding: utf-8 -*-

odoo.define('web_draggable_dialog', function (require) {
'use strict';

var Dialog = require('web.Dialog');

Dialog.include({
    opened: function (handler) {
        var self = this;
        return this._super(handler).done(function() {
            var draggable = self.$modal.draggable('instance');
                if (!draggable) {
                self.$modal.draggable({
                    handle: '.modal-header',
                    helper: false
                });
            }
        });
    },
});

});