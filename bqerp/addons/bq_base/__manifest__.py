# -*- coding: utf-8 -*-

{
    'name': 'BQ - Base',
    'version': '0.1',
    'category': 'BQ',
    'sequence': 80,
    'summary': 'BQ Apps Base',
    'description': 'BQ Apps Base',
    'author': "lnkdel",
    'website': 'http://www1.feicai.club',
    'images': [
        'static/src/img/default_employee_image.png',
    ],
    'depends': [
        'mail',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/bq_base_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
