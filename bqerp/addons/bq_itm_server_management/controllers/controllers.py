# -*- coding: utf-8 -*-
from odoo import http
import json


class BqItmServerManagement(http.Controller):
    @http.route('/bq_itm_server_management/bq_itm_server_management/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/bq_itm_server_management/servers/', auth='user')
    def list(self, **kw):
        print(kw.get('context'))
        records = http.request.env['bq.itm.server'].search([])
        servers = []
        for host in records.filtered(lambda n: len(n.host_id) == 0).sorted('name'):
            servers.append({
                'host': host,
                'guests': host.guest_ids.sorted('name')
            })
        return http.request.render('bq_itm_server_management.server_list', {
            'servers': servers,
        })

    @http.route('/bq_itm_server_management/test/', auth='none')
    def test(self, **kw):
        return http.request.httprequest.path

