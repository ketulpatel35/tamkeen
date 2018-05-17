from odoo import models


class HrHoliday(models.Model):
    _inherit = 'hr.holidays'

    def check_state(self):
        if self.state in ['leave_approved', 'validate']:
            return True
        else:
            return False
