# -*- coding: utf-8 -*-
{
    'name': 'BQ ITM - Asset',
    'summary': 'IT Management - Assets.',
    'description': """
        Track Employees' IT Assets.""",
    'author': "lnkdel",
    'website': "http://www1.feicai.club",
    'category': 'BQ ITM',
    'version': '0.1',
    'depends': ['mail', 'bq_base', 'bq_itm_base'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/bq_itm_asset_view.xml',
        'views/bq_itm_asset_template.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

