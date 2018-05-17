from odoo import models, fields, api, _


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.multi
    def name_get(self):
        """
        get proper name for department (business unit)
        :return:
        """
        if self._context.get('from_project'):
            result = []
            for record in self:
                if record.name:
                    result.append(
                        (record.id, record.name))
            return result
        else:
            return super(HrDepartment, self).name_get()