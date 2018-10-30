# -*- coding: utf-8 -*-
{
    'name': "api_base",

    'summary': """General api module of Odoo""",

    'description': """
        General api module of Odoo
    """,

    'author': "lnkdel",
    'website': "http://www.feicai.club",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],    
}