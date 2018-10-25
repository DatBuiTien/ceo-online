# -*- coding: utf-8 -*-
{
    'name': "CEO Online",
    'summary': """
        CEO Online System
    """,
    'description': """
        CEO online module
    """,

    'author': "Thanh Cong A Chau",
    'website': "http://www.vietinterview.com",
    'category': 'CEO Online System',
    'version': '1.0',

    'application': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'portal', 'product', 'account', 'crm'],

    # always loaded
    'data': [
        'data/install.xml',
        'data/mail.xml',
        'data/account.xml',
    ]
}
