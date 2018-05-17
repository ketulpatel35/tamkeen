# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tamkeen Tech
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Timesheet Management",
    'summary': 'Timesheet Management',
    'description': """
    """,
    'category': 'Timesheet Management',
    'version': '1.0',
    'depends': [
        'hr_contract','hr_timesheet_sheet','service_configuration_panel',
        'organization_structure','hr_employee_id','hr_employee_approval_tab',
        'org_payroll_lock_day'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_view.xml',
        'views/hr_timesheet_sheet_form_view.xml',
        'views/hr_employee_view.xml',
        'views/reminder_cron.xml',
        'views/templates.xml',
        'views/timesheet_configuration.xml',
        'views/timesheet_record_line_cron.xml',
        'views/menu_view.xml',
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
