import math
from odoo.exceptions import Warning
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OEDATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OEDATE_FORMAT
from odoo import fields, models, api, _
from pytz import timezone


class payroll_period_end_1(models.Model):
    _name = 'hr.payroll.period.end.1'
    _description = 'End of Payroll Period Wizard Step 1'

    _change_res = {
        'br100': 0,
        'br50': 0,
        'br10': 0,
        'br5': 0,
        'br1': 0,
        'cent50': 0,
        'cent25': 0,
        'cent10': 0,
        'cent05': 0,
        'cent01': 0,
        'done': False,
    }

