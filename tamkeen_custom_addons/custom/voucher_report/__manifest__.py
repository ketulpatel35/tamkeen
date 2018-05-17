# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Voucher Report',
    'version': '1.0',
    'category': 'Finance',
    'depends': [
        'account'
    ],
    'author': 'Bista Solutions',
    'description': """
This module will allow to generate report for voucher with same format of form.
==============================================================================
    """,
    'data': [
        'report_voucher_template_form.xml',
        'report_voucher.xml',
    ],
    'installable': True,
    'auto_install': False
}
