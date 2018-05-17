from odoo import models, fields, api


class StageConfigurations(models.Model):
    _name = 'stage.config'

    name = fields.Char('Button Name')
    dam_conf_line_id = fields.Many2one('dam.conf.line')
    dam_conf_id = fields.Many2one('dam.conf', 'Dam Conf')
    object = fields.Many2one('ir.model', 'Model')
    attachment_mandatory = fields.Boolean('Attachment Mandatory')
    required_fields = fields.Many2many('ir.model.fields',
                                       'stage_conf_req_fields_rel',
                                       'stage_conf_id', 'req_fields',
                                       'Required Fields')
    multi_user_all_ids = fields.One2many('multi.user.allocation',
                                         'stage_config_id', 'Multi User')
    sla_hours = fields.Integer('SLA Hours')
    action_id = fields.Many2one('ir.actions.server', string='Server Action',
                                help="Optional custom server action to "
                                     "trigger when stage change.")
    is_reject = fields.Boolean('Is Reject Stage')
    add_reject_btn = fields.Boolean('Add Reject Button')
    add_set_to_draft_btn = fields.Boolean('Add Set to Draft Button')
    set_to_draft_btn_name = fields.Char('Set to Draft Button Name')

    # reject_btn_name = fields.Char('Reject/Cancel Button Name',
    #                               default='Reject')

    @api.onchange('is_reject')
    def onchange_set_reject_validation(self):
        """
        :return:
        """
        if self.is_reject:
            self.add_reject_btn = False

    @api.onchange('add_reject_btn')
    def onchange_set_reject_but_validation(self):
        """
        :return:
        """
        if self.add_reject_btn:
            self.is_reject = False
