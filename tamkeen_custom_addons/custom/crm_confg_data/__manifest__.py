
{
    'name': 'CRM Configuration for Tamkeen Company',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'sequence': 2,
    'summary': 'Leads, Opportunities, Phone Calls',
    'description': """
Tamkeen Company Configuration for Odoo(OpenERP)
 Customer Relationship Management (CRM) Module
==============================================================================================

Desc.: This module is developed to customize
 the generic CRM model to suit Tamkeen company business process

Functionality: It only renames built-in opportunity stages and add new ones
""",
    'author': 'Tamkeen Company',
    'website': 'www.tamkeentech.sa',
    'depends': [
        'crm',
    ],
    'data': [
        'data/crm_lead_data.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
