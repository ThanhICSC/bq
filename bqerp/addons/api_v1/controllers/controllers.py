# -*- coding: utf-8 -*-
from odoo import http
import werkzeug
import json
from odoo.http import request


def json_response(rp):
    headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"}
    return werkzeug.wrappers.Response(json.dumps(rp, cls=MyEncoder, ensure_ascii=False), mimetype='application/json', headers=headers)


def json_except_response(rp, code, message):
    headers = {"Access-Control-Allow-Origin": "*",
               "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
               "Status": code,
               "Message": message}
    return werkzeug.wrappers.Response(json.dumps(rp, cls=MyEncoder, ensure_ascii=False),
                                      status=code,
                                      mimetype='application/json',
                                      headers=headers)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8');
        return json.JSONEncoder.default(self, obj)


class ApiV1(http.Controller):
    @http.route('/api/v1/getcfbproductionlines', type='http', auth="none", methods=['GET', 'POST'], csrf=False)
    def get_cfb_production_lines(self, token, fields=None, filter=None, page=None, per_page=None, order=None):
        if 'HTTP_X_REAL_IP' in request.httprequest.environ:
            remote = request.httprequest.environ['HTTP_X_REAL_IP']
        else:
            remote = request.httprequest.remote_addr

        ip = remote
        kw = dict(fields=fields, filter=filter, page=page, per_page=per_page, order=order)
        rp = request.env['base.api.base'].read_objects(token, kw, ip, 'hs.pts.cf.cfb.production.line', [1, 2], 'en')
        message = rp['message']
        code = rp['code']
        return json_except_response(rp, code, message)

    @http.route([
        '/api/v1/callmethoddemo',
    ], auth='none', type='http', csrf=False, methods=['POST', 'GET'])
    def call_method_demo(self, token, kw, model=None, method=None):
        if 'HTTP_X_REAL_IP' in request.httprequest.environ:
            remote = request.httprequest.environ['HTTP_X_REAL_IP']
        else:
            remote = request.httprequest.remote_addr

        ip = remote
        kw = dict(weight=1.1, remark='', length_standard='1500 ~ 5000', is_first_spindle_in_carton='False',
                  is_use_standard_weight='False', is_re_weight='False', execute_by=1)
        model = 'hs.pts.cf.cfb.spindle'
        method = 'weight'
        rp = request.env['base.api.base'].call_method(token, kw, ip, model, method)
        message = rp['message']
        code = rp['code']
        return json_except_response(rp, code, message)
