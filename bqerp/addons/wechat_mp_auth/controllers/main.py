# -*- coding: utf-8 -*-
# Copyright (C) 2018 MAXSNS Corp (http://www.maxsns.com)
# @author Henry Zhou (zhouhenry@live.com)
# License OPL-1 - See https://www.odoo.com/documentation/user/11.0/legal/licenses/licenses.html

import werkzeug
import requests
from odoo import http, fields
from odoo.http import request
from odoo.service import security
import logging
import datetime
import random

_logger = logging.getLogger(__name__)
target_url = "https://api.weixin.qq.com/sns/jscode2session"


def ensure_db():
    db = request.params.get('db') and request.params.get('db').strip()

    # Ensure db is legit
    if db and db not in http.db_filter([db]):
        db = None

    if db and not request.session.db:
        # User asked a specific database on a new session.
        request.session.db = db
        return

    # if db not provided, use the session one
    if not db and request.session.db and http.db_filter([request.session.db]):
        db = request.session.db

    # if no database provided and no database in session, use monodb
    if not db:
        db = http.db_monodb(request.httprequest)

    # always switch the session to the computed db
    if db != request.session.db:
        request.session.logout()

    request.session.db = db


def _get_open_id(code, appid):
    secret = request.env['ir.config_parameter'].sudo().get_param('wechat.mp.secret.' + appid, '')
    if not secret:
        raise RuntimeError('Cannot get App Secret parameter for ' + appid)
    params = werkzeug.url_encode({
        "appid": appid, "secret": secret, "js_code": code, "grant_type": "authorization_code"
    })
    result = requests.get(target_url, params=params).json()
    if "openid" in result and result["openid"]:
        return result["openid"]
    elif "errcode" in result:
        raise RuntimeError(('WeChat Server Error: %s ' + result["errmsg"]) % result["errcode"])
    else:
        raise RuntimeError('Unknown WeChat Server Error')


class WeChatMPAuth(http.Controller):

    @http.route('/wechat_mp_auth/logout', type='json', auth="user", methods=["POST"])
    def logout(self, appid, **kw):
        request.env['wechat.account'].sudo().search([('open_id', '=', request.session.wechat_openid),
                                                     ('app_id', '=', appid),
                                                     ('user_id', '=', request.env.user.id)]).unlink()
        request.session.logout(keep_db=True)
        return True

    @http.route('/wechat_mp_auth/get_user_info', type='json', auth="user", methods=["POST"])
    def get_user_info(self, **kw):
        return {
            'id': request.env.user.id,
            'name': request.env.user.name
        }

    @http.route('/wechat_mp_auth/auth_by_login', type='json', auth="none", methods=["POST"])
    def auth_by_login(self, code, appid, login, pwd, **kw):
        ensure_db()
        if login and pwd:
            uid = request.session.authenticate(request.session.db, login, pwd)
            if uid:
                try:
                    openid = _get_open_id(code, appid)
                except RuntimeError as e:
                    return {'error': 'wechat_error', 'message': '%s' % e}
                account = request.env['wechat.account'].sudo().search(
                    [('open_id', '=', openid), ('app_id', '=', appid)])
                if account:
                    if account.user_id.id != uid:
                        account.write({'user_id': uid})
                else:
                    request.env['wechat.account'].sudo().create({
                        'open_id': openid,
                        'user_id': uid,
                        'app_id': appid,
                    })
                request.session.wechat_openid = openid
                user = request.env['res.users'].sudo().browse(uid)
                return {
                    'success': 'You have been logged in successfully!',
                    'user_name': user.name,
                    'user_id': uid,
                }
        return {'error': 'invalid_login', 'message': 'Invalid login name or password.'}

    @http.route('/wechat_mp_auth/auth_by_code', type='json', auth="none", methods=["POST"])
    def auth_by_code(self, code, appid, **kw):
        ensure_db()
        try:
            openid = _get_open_id(code, appid)
        except RuntimeError as e:
            return {'error': 'wechat_error', 'message': '%s' % e}
        account = request.env['wechat.account'].sudo().search(
            [('open_id', '=', openid), ('app_id', '=', appid)])
        if account:
            request.session.uid = account.user_id.id
            request.session.login = account.user_id.login
            request.session.session_token = security.compute_session_token(request.session)
            request.uid = account.user_id.id
            request.disable_db = False
            request.session.get_context()
            request.session.wechat_openid = openid
            return {
                'success': 'You have been logged in successfully!',
                'user_name': account.user_id.name,
                'user_id': account.user_id.id,
            }
        else:
            return {'error': 'auth_failed', 'message': 'Authenticating failed, login required.'}

