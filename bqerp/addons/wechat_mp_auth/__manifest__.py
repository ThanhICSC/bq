# -*- coding: utf-8 -*-
# Copyright (C) 2018 MAXSNS Corp (http://www.maxsns.com)
# @author Henry Zhou (zhouhenry@live.com)
# License OPL-1 - See https://www.odoo.com/documentation/user/11.0/legal/licenses/licenses.html
{
    'name': 'Wechat Mini Program Auth',
    'author': "MAXSNS",
    'website': "http://www.maxsns.com",
    'category': 'web',
    'version': '1.0.0',
    'depends': [
    	'wechat_account',
    ],
    'data': [
        'data/config.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,

    'license': 'OPL-1',
    'price': 99.00,
    'currency': 'EUR',
}
