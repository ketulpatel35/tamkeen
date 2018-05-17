# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': "Cron Failure Notification",
    'version': '10.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """
        Cron jobs/Scheduled Actions failure Log Notification & Its
        PDF Reports
    """,
    'description': """
        This module will generate error Logs for Scheduled
        Actions / Cron jobs running in backend server
    """,
    'author': "Bista Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "http://www.bistasolutions.com",
    'depends': ['base', 'mail', 'web', 'base_setup'],
    'data': [
        'views/logs_scheduled_actions_view.xml',
        'views/error_log_report_template.xml',
        'views/report.xml',
        'views/error_mail_template.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
