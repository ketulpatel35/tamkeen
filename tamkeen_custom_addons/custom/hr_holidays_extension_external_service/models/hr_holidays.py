from odoo import models, api, fields, _
from odoo.exceptions import Warning


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    external_manager_response = fields.Selection([('approved', 'Approved'),
                                                  ('rejected', 'Rejected')],
                                                 string='External Manager '
                                                        'Response')
    external_manager_approval_date = fields.Datetime(string='External Manager '
                                                            'Approval Date',
                                                     copy=False)
    external_manager_user_id = fields.Many2one('res.users',
                                               string='External Manager '
                                                      'Approval',
                                               copy=False)

    @api.multi
    def confirm_mgt(self):
        for rec in self:
            if rec.employee_id.outside_employee and \
                    rec.external_manager_response != 'approved':
                raise Warning(_('To proceed, The external manager '
                                'should approve the request.'))
        return super(HrHolidays, self).confirm_mgt()