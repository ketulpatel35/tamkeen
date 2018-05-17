from odoo import models, fields, api
from datetime import datetime


class BlacklistVendor(models.TransientModel):
    _name = 'blacklist.vendor'

    @api.multi
    def blacklistvendor(self):
        """
        manage active - inactive of supplier and child-supplier.
        :return:
        """
        context = dict(self._context) or {}
        current_date = str(datetime.now().date())
        reason = str(self.reason)
        user_rec = self.env['res.users'].browse(self.env.uid)
        if context and context.get('is_vendor'):
            vendor_rec = self.env['res.partner'].browse(
                context.get('active_id'))
            if vendor_rec:
                notes = str(vendor_rec.comment) + '\n' \
                    if vendor_rec.comment else ' '
                notes += '[ Blacklisted by: ' if context.get('active') \
                    else ''
                notes += '[ Un Blacklisted by: ' if not context.get('active') \
                    else ''
                notes += str(
                    user_rec.name) + ' : ' + current_date + '] ' + reason
                vendor_rec.write({'comment': notes})
                vendor_rec.toggle_active()
                # if not context.get('active'):
                #     vendor_reg = self.env['vendor.registration'].search([
                #         ('email', '=', vendor_rec.email),
                #         ('name', '=', vendor_rec.name)],
                #         limit=1)
                #     vendor_reg.is_black_list = True
                # vendor_reg_rec = self.env['vendor.registration'].search([
                #     ('partner_id', '=', vendor_rec.id)])
                # if vendor_reg_rec:
                #     vendor_reg_rec.is_black_list = \
                #         not vendor_reg_rec.is_black_list
        else:
            vendor_rec = self.env['vendor.registration'].browse(
                context.get('active_id'))
            if vendor_rec:
                notes = str(vendor_rec.notes) + '\n' \
                    if vendor_rec.notes else ' '
                notes += '[ Blacklisted by: ' if context.get('active') \
                    else ''
                notes += '[ Un Blacklisted by: ' if not context.get('active') \
                    else ''
                notes += str(
                    user_rec.name) + ' : ' + current_date + '] ' + reason
                if context.get('active'):
                    vendor_rec.with_context({'state_black_list': True}).write({
                        'notes': notes,
                        'is_black_list': False,
                        'state': 'blacklist'})
                    if vendor_rec.partner_id:
                        vendor_rec.partner_id.active = False
                        for child_rec in vendor_rec.child_ids:
                            if child_rec.partner_id:
                                child_rec.partner_id.active = False
                else:
                    # update last state
                    state = 'draft'
                    if len(vendor_rec.stage_logs) >= 2:
                        stage_log_rec = vendor_rec.stage_logs[-2]
                        if stage_log_rec:
                            state = stage_log_rec.stage
                    vendor_rec.with_context({'state_black_list': True}).write(
                        {'notes': notes, 'is_black_list': True,
                         'state': state})
                    if vendor_rec.partner_id:
                        vendor_rec.partner_id.active = True
                        for child_rec in vendor_rec.child_ids:
                            child_rec.partner_id.active = True
        return {'type': 'ir.actions.act_window_close'}

    reason = fields.Text(string='Reason')
