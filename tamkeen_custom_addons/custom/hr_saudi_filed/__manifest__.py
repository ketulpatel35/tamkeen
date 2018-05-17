# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Saudi HR Additional Fields',
    'version': '0.1',
    'sequence': 100,
    'category': 'Human Resources',
    "author": "Bista Solutions",
    "website": "http://www.bistasolutions.com",
    'summary': 'Saudi HR Additional Fields (GOSI, Iqama number...etc)',
    'description': """

This module adds the following:
================================

    * HR additional fields for Saudi employees such as GOSI, Iqama number..etc.
    * English name field mandatory
    * Work phone field non-mandatory
    * Filter Working Address field from employees names
    * Filter Home Address from employees names
    * Hide Coach field (non-usable)
    * When the employee is Saudi, Identification ID details only appear
    * When the employee is foreign, Iqama Number details only appear
    * Religion field mandatory
    * Home Address field non-mandatory
    * Identification No, ID Expiry Date, ID Expiry Date Hijri fields
    mandatory in case of Saudi employee
    * Passport No, Passport Expiry Date, Passport Expiry Date Hijri fields
    mandatory in case of foreign employee
    * P.O. Box, Zip Code new fields


""",
    'depends': [
        'base',
        'mail',
        'board',
        'hr',
        'hr_holidays',
        'hr_contract',
        'hr_employee_customization',
        'hr_employee_id',
    ],
    'data': [
        'views/family_information_view.xml',
        'views/hr_saudi_view.xml',
    ],
    'images': [],
    # 'update_xml' : ['security/security.xml','security/ir.model.access.csv'],

    'demo': [],

    'installable': True,
    'application': True,
}
