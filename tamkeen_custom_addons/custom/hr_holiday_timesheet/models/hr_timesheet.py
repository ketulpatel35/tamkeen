# -*- coding: utf-8 -*-
# © 2017 Jerome Guerriat
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api
from odoo.exceptions import UserError


class HRTimesheetSheet(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'

    @api.multi
    def unlink(self):
        for ts in self:
            if any(line.leave_id for line in ts.timesheet_ids):
                raise UserError(
                    'You cannot delete a timesheet with leave entries'
                )
        return super(HRTimesheetSheet, self).unlink()
