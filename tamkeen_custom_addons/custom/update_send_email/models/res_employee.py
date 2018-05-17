from odoo import models, fields


class ResEmployee(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        for rec in self:
            if vals.get('user_id'):
                data_pool = self.env['ir.model.data']
                template_pool = self.env['mail.template']
                template_id = \
                    data_pool.get_object_reference('update_send_email',
                                                   'employee_leave_request')[1]
                template_rec = template_pool.browse(template_id)
                if template_rec:
                    template_rec.send_mail(rec.id, force_send=False)
        res = super(ResEmployee, self).write(vals)
        return res