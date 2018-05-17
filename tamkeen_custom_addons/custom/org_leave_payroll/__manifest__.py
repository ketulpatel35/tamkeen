# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Leave Payroll",
    'summary': 'Organization Leave Payroll',
    'description': """
Organization Leave Payroll
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'hr_holidays_extension',
        'hr_payroll_period'
    ],
    'data': [
        # 'views/hr_holidays_view.xml'
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
