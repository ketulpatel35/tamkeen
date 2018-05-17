# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Salary Certificate Report",
    "version": "10.0",
    "category": "Human Resources Payslip",
    "license": "AGPL-3",
    "description": """

    """,
    "author": "Bista solutions",
    "website": "http://www.bistasolutions.com",
    "depends": ["hr", "hr_payroll"],
    'data': ["reports/salary_certificate_detail_report_template.xml",
             "reports/salary_certificate_embassy_report_template.xml",
             "reports/salary_certificate_gross_report_template.xml",
             "reports/salary_certificate_no_report_template.xml",
             "views/register_report.xml",
             ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
