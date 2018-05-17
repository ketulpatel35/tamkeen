# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Recruitment Customization',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 100,
    'category': 'Human Resources',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Add more fields to Applications form',
    'description':
        """
        This module do the following:

            1- Add following fields to Applications form
                * Gender
                * Nationality
                * University
                * University Location
                * Major
                * Other Major
                * Minor
                * GPA
                * Expected Graduation Year
                * Expected Graduation Month
                * Years of Experience

            2- Customize the degree data
                * Change name "Graduate" to "High School"
                * Add new "Diploma"
                * Change name "Doctoral Degree" to "Doctoral Degree PhD"
                * Arrange degree data according to education level

            #Openinside addition:

            3- Add security file

            4- Add following fields to Applications form
                * Date of Birth
                * Current Location
                * Grid Table (References)
        """,
    'depends': [
        'hr_recruitment',
        'base',
    ],
    'data': [
        'security/groups.xml',
        'static/data/degree_data.xml',
        'static/data/major_data.xml',
        # 'views/hr_recruitment_customization.xml',
        'security/ir.model.access.csv',
    ],
    'images': [],
    'update_xml': [],

    'demo': [],

    'installable': True,
    'application': True,
}
