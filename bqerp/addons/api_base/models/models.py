# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.modules.registry import Registry
import datetime
from odoo.exceptions import UserError
from .tokenbucket import token_bucket

try:
    import redis
except (ImportError, AssertionError):
    raise UserError('Redis not available. Please install "redis" python package.')


def redis_connect():
    return redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


def authenticate_token(token, lang=None):
    if not token:
        return None

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
                return register(db, uid, lang)
            else:
                return None
        else:
            return None


def register(db, uid, lang=None):
    registry = Registry(db)
    cr = registry.cursor()
    context = {lang: lang} if lang else {}
    env = api.Environment(cr, int(uid), context)
    return env


def invalid_token():
    return {'success': False, 'code': 401, 'message': 'invalid token!'}


def forbidden():
    return {'success': False, 'code': 403, 'message': 'forbidden'}


class ApiBase(models.AbstractModel):
    _name = 'base.api.base'

    # todo: get accept-language from client, set the context
    # todo: access frequency, by uid,ip 2018/1/22
    def read_objects(self, token, kw, access_ip, model=None, ids=None, lang=None):
        if not token_bucket(1, access_ip):
            return forbidden()

        code, success, message, result, count, offset, limit = 200, True, '', '', 0, 0, 80
        if not kw.get('filter'):
            domain = []
        elif isinstance(kw.get('filter'), str):
            if '[' in kw.get('filter'):
                domain = eval(kw.get('filter'))
            else:
                domain = kw.get('filter').split(',')
        elif isinstance(kw.get('filter'), list):
            domain = kw.get('filter')

        if not kw.get('fields'):
            fields = []
        elif isinstance(kw.get('fields'), str):
            if '[' in kw.get('fields'):
                fields = eval(kw.get('fields'))
            else:
                fields = kw.get('fields').split(',')
        elif isinstance(kw.get('fields'), list):
            fields = kw.get('fields')

        offset = (kw.get('page') or 1) - 1
        limit = kw.get('per_page') or 80
        order = kw.get('order') or 'id'

        env = authenticate_token(token, lang)
        if not env:
            return invalid_token()

        if ids:
            if isinstance(ids, str):
                ids = map(int, ids.split(','))
            elif isinstance(ids, list):
                ids = ids
            domain += [('id', 'in', ids)]

        try:
            count = env[model].search_count(domain)
            result = env[model].search_read(domain, fields, offset*limit, limit, order)
            model_fields = env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0],'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
        except Exception as e:
            code, result, success, message = 500, '', False, str(e)
        return {'success': success, 'code': code, 'message': message, 'result': result,
                'total': count, 'page': offset+1, 'per_page': limit}


    def create_objects(self, token, kw, access_ip, model=None, lang=None):
        if not token_bucket(1, access_ip):
            return forbidden()

        success, message = True, ''
        env = authenticate_token(token, lang)

        if not env:
            return invalid_token()

        try:
            result = env[model].create(kw).id
        except Exception as e:
            result, success, message = '', False, str(e)
        env.cr.commit()
        env.cr.close()
        rp = {'result': result, 'success': success, 'message': message}
        return rp


    def unlink_objects(self, token, access_ip, model=None, ids=None):
        if not token_bucket(1, access_ip):
            return forbidden()

        env = authenticate_token(token)
        if not env:
            return invalid_token()

        if ids:
            ids = map(int, ids.split(','))

        try:
            result = env[model].browse(ids).unlink()
        except Exception as e:
            result, success, message = '', False, str(e)
        env.cr.commit()
        env.cr.close()
        rp = {'result': result,}
        return rp


    def call_method(self, token, kw, access_ip, model=None, method=None, lang=None):
        if not token_bucket(1, access_ip):
            return forbidden()

        code, success, message = 200, True, ''
        env = authenticate_token(token, lang)
        if not env:
            return invalid_token()

        try:
            result = eval('env[model].'+method)(kw)
        except Exception as e:
            code, result, success, message = 500, '', False, str(e)
        env.cr.commit()
        env.cr.close()
        response = {'result': result, 'code': code, 'success': success, 'message': message}
        if isinstance(result, dict) and result.get('pagination'):
            response.update(result.pop('pagination'))
            response.update({'result': result.pop('results')})
        return response
