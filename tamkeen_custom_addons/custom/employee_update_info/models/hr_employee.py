from odoo import models, api, fields, _
# from datetime import datetime, date, timedelta
# from dateutil.relativedelta import relativedelta
# from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
# from odoo.exceptions import Warning
# from openerp.exceptions import UserError
# from days360 import get_date_diff_days360


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _check_group(self, group_xml_id_lst):
        user_rec = self.env.user
        for group_xml_id in group_xml_id_lst:
            if user_rec.has_group(str(group_xml_id)):
                return True
        return False

    @api.multi
    def compute_is_self_employee(self):
        for rec in self:
            is_self_employee = False
            if rec.user_id.id == self.env.user.id:
                is_self_employee = True
            else:
                is_self_employee = self._check_group([
                    'hr_employee_customization.group_create_emp_profile',
                    'hr_employee_customization.group_update_emp_info',
                    'hr_employee_customization.group_view_emp_info'])
            rec.is_self_employee = is_self_employee

    is_self_employee = fields.Boolean(
        compute='compute_is_self_employee', string='Same Employee?',
        invisible="1",
        help='Employee can view/update his own data.')
