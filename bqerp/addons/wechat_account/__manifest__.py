# -*- coding: utf-8 -*-
# Copyright (C) 2018 MAXSNS Corp (http://www.maxsns.com)
# @author Henry Zhou (zhouhenry@live.com)
# License OPL-1 - See https://www.odoo.com/documentation/user/11.0/legal/licenses/licenses.html
{
    'name': 'WeChat Account',
    'author': "MAXSNS",
    'website': "http://www.maxsns.com",
    'category': 'web',
    'version': '1.0.0',
    'depends': [
    	'base',
    ],
    'data': [
        'views/res_users.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,

    'license': 'OPL-1',
}
