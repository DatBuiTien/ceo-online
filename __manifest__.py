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
    'depends': ['base', 'mail', 'portal', 'account', 'crm'],
    'sequence': 1,
    # always loaded
    'data': [
        'data/install.xml',
        'data/mail.xml',
        'data/account.xml',
        'views/group_view.xml',
        'views/course_view.xml',
        'views/learning_path_view.xml',
        'views/enrollment_view.xml',
        'views/customer_learner_view.xml',
        'views/payment_request_view.xml',
        'views/web_page_view.xml',
        'views/user_view.xml',
        'views/permission_view.xml',
        'views/reset_pass_token_view.xml',
        'views/menu_view.xml',
    ]
}
