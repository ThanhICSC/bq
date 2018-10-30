# -*- coding: utf-8 -*-
{
    'name': "api_v1",

    'summary': """
        Odoo Web Api V1""",

    'description': """
        Odoo Web Api V1
    """,

    'author': "lnkdel",
    'website': "http://www.feicai.club",
    
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'api_base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    
}