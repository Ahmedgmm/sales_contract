{
    'name': 'Sales Contract Approval & Limits',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Manage contracts with approval teams and limit sales orders based on contract balance.',
    'author': 'Your Company',
    'depends': ['sale', 'mail', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_team_views.xml',
        'views/sale_contract_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
}