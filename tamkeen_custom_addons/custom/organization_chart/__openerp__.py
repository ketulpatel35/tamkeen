{
    'name': 'Generic Tree Charts',
    'category': 'Tools',
    'summary': 'Generic Tree Charts',
    'version': '1.0',
    'description': """
Generic Tree Charts:
########################################
- You can create any kind of parent/child trees.
- You can customize the display theme as you want.
- You can control the display of the fields that you selected to be displayed.
        """,
    'author': 'Tamkeen Technologies',
    'depends': ['base','website'],     
    
    'data': [
        'security/tree_chart_security.xml',
        'security/ir.model.access.csv',
        # 'security/ir_rule.xml',
        'views/organization_chart_view.xml',
        'views/organization_chart_template.xml',
        'views/tree_chart_config_view.xml',
    ],
    'qweb': [],
    'installable': True,
}
