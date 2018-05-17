{
    'name': 'Asset Location',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'depends': ['account_asset'],
    'author': 'Bista Solutions',
    'description': """
    This module will modify allow to configure and assign asset to specific location
    """,
    'website': 'https://bistasolutions.com',
    'data': [
        'security/asset_location_security.xml',
        'security/ir.model.access.csv',
        'views/account_asset_view.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False
}
