# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Date Range",
    "summary": "Manage all kind of date range",
    "version": "9.0.1.0.0",
    "category": "Uncategorized",
    "author": "Bista Solutions",
    "website": "http://www.bistasolutions.com",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/date_range_security.xml",
        "views/assets.xml",
        "views/date_range_view.xml",
        "wizard/date_range_generator.xml",
    ],
    "qweb": [
        "static/src/xml/date_range.xml",
    ]
}
