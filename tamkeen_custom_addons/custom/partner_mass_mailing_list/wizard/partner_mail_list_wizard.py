from odoo import models, api, fields


class PartnerMailListWizard(models.TransientModel):
    _name = "partner.mail.list.wizard"
    _description = "Create contact mailing list"

    mail_list = fields.Many2one(comodel_name="mail.mass_mailing.list",
                                string="Mailing List")
    partners = fields.Many2many(comodel_name="res.partner",
                                relation="mail_list_wizard_partner")

    @api.multi
    def add_to_mail_list(self):
        contact_obj = self.env['mail.mass_mailing.contact']
        partner_obj = self.env['res.partner']
        for partner_id in self.env.context.get('active_ids', []):
            partner = partner_obj.browse(partner_id)
            criteria = [('email', '=', partner.email),
                        ('list_id', '=', self.mail_list.id)]
            contact_test = contact_obj.search(criteria)
            if contact_test:
                continue
            contact_vals = {
                'email': partner.email,
                'name': partner.name,
                'list_id': self.mail_list.id
            }
            contact_obj.create(contact_vals)
