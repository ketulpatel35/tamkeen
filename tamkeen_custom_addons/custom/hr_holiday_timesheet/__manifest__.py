# -*- coding: utf-8 -*-
# © 2017 Jerome Guerriat
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Timesheet - Include leave',
    'category': 'HR',
    'summary': 'Keep track of your leave directly from your timesheet',
    'website': 'http://www.niboo.be',
    'license': 'AGPL-3',
    'version': '10.0.1.0.0',
    'description': '''
    Keep an overview of your leave by having them displayed directly on your timesheet.
    As soon as a leave is approved, it will show up on the employee's timesheet on a designated line.
        ''',
    'author': 'Niboo',
    'depends': [
        'hr_timesheet_sheet',
        'hr_holiday_exclude_special_days',
    ],
    'data': [
        'data/holiday_timesheet_data.xml',
        'views/view_holiday_request.xml',
    ],
    'images': [
      'static/description/hr_holiday_timesheet_cover.png',
    ],
    'installable': True,
    'application': False,
}
