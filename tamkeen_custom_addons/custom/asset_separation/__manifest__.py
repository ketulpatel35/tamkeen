{
    'name': 'Asset Separation',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'depends': ['account_asset'],
    'author': 'Bista Solutions',
    'description': """
    This module will modify the function
    that creates assets, when create new
    supplier invoice/asset line with multiple
     quantity. It will create asset record
      for each one in the qatity
    """,
    'website': 'https://bistasolutions.com',
    'data': ['views/account_assets_inherit.xml', ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False
}
