# -*- coding: utf-8 -*-
{
    'name': 'Contract-Based Sales Limitation',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Restrict sales based on approved contracts with approval team limits',
    'description': """
        This module allows you to:
        - Link sales orders to contracts
        - Require approved contracts before confirming sales
        - Set contract approval teams with amount limits
        - Track contract usage and remaining amounts
        - Prevent sales without valid approved contracts
    """,
    'author': 'Your Company',
    'depends': ['sale_management', 'contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_views.xml',
        'views/contract_approval_team_views.xml',
        'views/sale_order_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
