//-*- coding: utf-8 -*-

odoo.define('web_frozen_list_view_header', function (require) {
'use strict';

var ListRenderer = require('web.ListRenderer');

ListRenderer.include({
    _renderView: function () {
        var self = this;
        return this._super().done(function () {
            var form_field_length = self.$el.parents('.o_form_field').length;
            var scrollArea = $(".o_content")[0];
            function do_freeze () {
                self.$el.find('table.o_list_view').each(function () {
                    $(this).stickyTableHeaders({scrollableArea: scrollArea, fixedOffset: 0.1});
                });
            }

            if (form_field_length == 0) {
                do_freeze();
                $(window).unbind('resize', do_freeze).bind('resize', do_freeze);
            }
        });
    },
});

});