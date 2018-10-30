# -*- coding: utf-8 -*-
from odoo import api, http, _
from odoo.modules.registry import Registry
import werkzeug
import base64
import time
import json
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

TOKEN_LIFE_DAYS = 70

try:
    import redis
except (ImportError, AssertionError):
    raise UserError('Redis not available. Please install "redis" python package.')


def no_token():
    rp = {'result': '', 'success': False, 'message': 'invalid token!'}
    return json_response(rp)


def json_response(rp):
    headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"}
    return werkzeug.wrappers.Response(json.dumps(rp, ensure_ascii=False), mimetype='application/json', headers=headers)


def authenticate(token):
    try:
        a = 4 - len(token) % 4
        if a != 0:
            token += '==' if a == 2 else '='
        SERVER, db, login, uid, ts = base64.urlsafe_b64decode(str(token)).split(',')
        if int(ts) + 60*60*24*7*10 < time.time():
            return False
        registry = Registry(db)
        cr = registry.cursor()
        env = api.Environment(cr, int(uid), {})
    except Exception as e:
        return str(e)
    return env


def register(db, uid):
    registry = Registry(db)
    cr = registry.cursor()
    env = api.Environment(cr, int(uid), {})
    return env


def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


def get_exists_item_in_redis(r, uid):
    keys = r.keys()
    for key in keys:
        if ':' not in key:
            value = eval(r.get(key))
            if value['uid'] == uid:
                return value
    return None


def store_token(user_token):
    r = redis_connect()
    token = user_token['token']
    uid = user_token['uid']
    effective_time = user_token['effective_time']

    token_exists = get_exists_item_in_redis(r, uid)
    if not token_exists:
        r.set(token, user_token)
        return token
    else:
        token_exists_key = token_exists['token']
        if effective_time > token_exists['expiration_time']:
            r.delete(token_exists_key)
            r.set(token, user_token)
            return token
        else:
            return token_exists_key


def refresh_token(token, current_time):
    r = redis_connect()
    value = r.get(token)
    if not value:
        return None
    else:
        user_token = eval(value)
        if user_token:
            expiration_time = user_token['expiration_time']
            if current_time <= expiration_time:
                new_token = base64.urlsafe_b64encode(str(time.time() * 1000)).replace('=', '')
                new_user_token_object = {
                    'server': '127.0.0.1',
                    'db_name': user_token['db_name'],
                    'login_name': user_token['login_name'],
                    'uid': int(user_token['uid']),
                    'token': new_token,
                    'effective_time': current_time,
                    'expiration_time': current_time + relativedelta(days=TOKEN_LIFE_DAYS)
                }
                r.delete(token)
                r.set(new_token, new_user_token_object)
                return new_token
            else:
                return None
        else:
            return None


def delete_token(token):
    r = redis_connect()
    r.delete(token)
    return True


def authenticate_token(token):
    r = redis_connect()
    value = r.get(token)
    if not value:
        return None
    else:
        user_token = eval(value)
        if user_token:
            expiration_time = user_token['expiration_time']
            if datetime.datetime.now() <= expiration_time:
                uid = int(user_token['uid'])
                db = user_token['db_name']
                return register(db, uid)
            else:
                return None
        else:
            return None


class ApiBase(http.Controller):
    @http.route([
        '/api/v1.0/get_token',
    ], type='http', auth="none", csrf=False, methods=['POST', 'GET'])
    def get_token(self, login=None, pwd='admin', db='d10', **kw):
        success, message = True, ''
        try:
            uid = http.request.session.authenticate(db, login, pwd)
        except Exception as e:
            rp = {'token': '', 'success': False, 'message': str(e)}
            return json_response(rp)
        if not uid:
            rp = {'token': '', 'success': False, 'message': 'you are unauthenticated'}
            return json_response(rp)

        now = datetime.datetime.now()
        expiration = now + relativedelta(days=TOKEN_LIFE_DAYS)
        # token = base64.urlsafe_b64encode(str(round(time.time() * 1000))).replace('=', '')
        token = str(base64.urlsafe_b64encode(bytes(str(round(time.time() * 1000)), encoding="utf8"))).replace('=', '')

        user_token = {
            'server': '127.0.0.1',
            'db_name': db,
            'login_name': login,
            'uid': uid,
            'token': token,
            'effective_time': now,
            'expiration_time': expiration
        }
        real_token = store_token(user_token)

        rp = {'token': real_token, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v1.0/refresh_token',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def refresh_token(self, **kw):
        success, message = True, ''
        token = kw.pop('token')
        new_token = refresh_token(token)
        if not new_token:
            return no_token()
        else:
            rp = {'token': new_token, 'success': success, 'message': message}
            return json_response(rp)

    @http.route([
        '/api/v1.0/delete_token',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def delete_token(self, **kw):
        token = kw.pop('token')
        result = delete_token(token)
        rp = {'result': result, }
        return json_response(rp)