# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tamkeen Tech
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Time Recording Payroll",
    'summary': 'Organization Time Recording Payroll',
    'description': """
    """,
    'category': 'Timesheet',
    'version': '1.0',
    'depends': [
        'hr_payroll',
        'hr_overtime',
        'org_shift_timeline',
        'product',
        # 'hr_payroll_period',
        'web_readonly_bypass',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sheet_time_record_line_view.xml',
        'views/time_recording_configuration.xml',
        # 'views/hr_payroll_view.xml',
        'views/timesheet_record_line_cron.xml',
        'views/menu_view.xml',
        'wizard/time_record_action_view.xml'
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Tamkeen Tech',
    'maintainer': 'tamkeentech.sa',
    'website': 'http://tamkeentech.sa',
    'license': 'AGPL-3',
    'demo': [],
    'test': [],
    'installable': True,
}
