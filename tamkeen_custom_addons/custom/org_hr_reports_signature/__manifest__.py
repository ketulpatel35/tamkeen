# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "PaySlip Detail Report Configuration",
    'summary': 'PaySlip Detail Report Configuration',
    'description': """
PaySlip Detail Report Configuration
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'org_payroll_lock_day',
    ],
    'data': [
        'views/res_company_view.xml',
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Bistasolutions.com',
    'maintainer': 'bistasolutions.com',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    # Technical options
    'demo': [],
    'test': [],
    'installable': True,
    # 'auto_install':False,
    # 'active':True,
}
