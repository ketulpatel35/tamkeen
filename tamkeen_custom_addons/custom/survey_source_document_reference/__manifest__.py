# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Survey Source Document Reference',
    'version': '1.0',
    'author': 'BistaSolutions',
    'sequence': 7,
    'category': 'Services',
    'website': 'http://www.bistasolutions.com/',
    'summary': 'Survey Source Document Reference',
    'description': """
- linkup different objects with survey
""",
    'depends': [
        'base', 'survey'
    ],
    'data': [
        'views/survey_views.xml',
    ],
    'images': [],
    'update_xml': [],
    'demo': [],
    'installable': True,
    'application': True,
}
