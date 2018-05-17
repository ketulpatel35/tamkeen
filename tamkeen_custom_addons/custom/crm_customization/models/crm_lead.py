from odoo import models, fields, api, _


class CrmAttachment(models.Model):
    _name = 'crm.attachment'

    name = fields.Char(string='Name')
    description = fields.Text('Description')
    mandatory = fields.Boolean('Mandatory')
    document = fields.Binary('Document')
    document_file_name = fields.Char('File Name')
    lead_id = fields.Many2one('crm.lead', string='Opportunity')


class CrmProposal(models.Model):
    _name = 'crm.proposal'

    assignment_date = fields.Date(string='Assignment Date')
    planned_start_date = fields.Date(string='Planned Start Date')
    proposal_writing_duration = fields.Float(
        string='Planned Proposal Writing Duration')
    planned_review_duration = fields.Float(string='Planned Review Duration')
    planned_release_date = fields.Date(string='Planned Release '
                                              'Date')
    actual_start_date = fields.Date(string='Actual Start Date')
    actual_release_date = fields.Date(string='Actual Release Date')
    total_proposal_value = fields.Float(string='Total Proposal Value')
    proposal_status = fields.Selection([('new', 'New'), ('writing',
                                                         'Writing'),
                                        ('submitted', 'Submitted'),
                                        ('re_submitted', 'Re-Submitted')],
                                       default='new')
    lead_id = fields.Many2one('crm.lead', string='Opportunity')


class CrmBiddding(models.Model):
    _name = 'crm.bidding'

    submission_date = fields.Date(string='Submission Date')
    bid_status = fields.Selection([('new', 'New'), ('bids', 'Bids'),
                                   ('submitted', 'Submitted'),
                                   ('evaluated', 'Evaluated'), ('win', 'Win'),
                                   ('loss', 'Loss'), ('cancelled',
                                                      'Cancelled')],
                                  string='Bid Status', default='new')
    financial_proposal_ranking = fields.Integer(string='Financial Proposal '
                                                       'Ranking')
    guarantee_issue = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                       string='Guarantee Issue')
    saudi_certificate = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                         string='Saudization Certificate')
    bid_notes = fields.Text(string='Bid Notes')
    bid_questions = fields.Text(string='Bid Questions')
    lead_id = fields.Many2one('crm.lead', string='Opportunity')



class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # @api.depends('planned_start_date', 'proposal_writing_duration',
    #              'planned_review_duration')
    # def _get_planned_release_date(self):
    #     for rec in self:
    #         planned_start_date = False
    #         if rec.planned_start_date:
    #             print 'AAAAAA', rec.planned_review_duration
    #             planned_start_date = rec.planned_start_date + relativedelta(
    #                 days=(
    #                     float(rec.proposal_writing_duration) +
    #                     float(rec.planned_review_duration)))
    #         rec.planned_release_date = planned_start_date

    bid_type = fields.Selection([('rfp', 'RFP'), ('closed_bid', 'Closed '
                                                                'Bid'),
                                 ('direct_bid', 'Direct Bid'), ('other',
                                                                'Other')])
    proposal_submission_date = fields.Date(string='Proposal Submission Date')
    last_question_date = fields.Date(string='Last Question Date')
    language_id = fields.Many2one('res.lang', string='Proposal Language')
    qualification_status = fields.Selection([('pass', 'Pass'), ('fail',
                                                                'Fail')],
                                            string='Qualification Status')
    estimated_budget = fields.Float(string='Estimated Budget')
    client_type = fields.Selection([('existing', 'Existing'), ('prospect',
                                                               'Prospect'),
                                    ('other', 'Other')], string='Client Type')
    method = fields.Selection([('in_person', 'In Person'), ('social_media',
                                                            'Social Media'),
                               ('email', 'Email')], string='Method')
    reported_by = fields.Char(string='Reported By')
    project_type = fields.Selection([('sub_contract', 'Sub contract'),
                                     ('vendor', 'Vendor'),
                                     ('copany_services', 'Company '
                                                         'Services'),
                                     ('profit_sharing', 'Profit Sharing')],
                                    string='Project Type')
    opportunity_analysis = fields.Text(string='Opportunity Analysis')

    proposal_ids = fields.One2many('crm.proposal', 'lead_id',
                                  string='Proposal/s')
    bidding_ids = fields.One2many('crm.bidding', 'lead_id',
                                     string='Bidding/s')
    attachment_ids = fields.One2many('crm.attachment', 'lead_id',
                                     string='Attachment/s')


    @api.multi
    def forward_to_account_manager(self):
        '''
        This function opens a window to compose
         an email, with the edi sale
          template message loaded by default
        '''

        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference(
                    'crm_customization',
                    'email_update_forward_to_account_manager')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'crm.lead',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_message_type': 'email',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

        # @api.multi
        # def unlink(self):
        #     for rec in self:
        #         if not rec.user_id.id == self.env.uid:
        #             raise Warning(
        #                 _("You should have access for delete this "
        #                   "lead/opportunity."))
        #     return super(CrmLead, self).unlink()
        #
        # @api.multi
        # def write(self, vals):
        #     for rec in self:
        #         user_id = vals.get('user_id') or rec.user_id.id
        #         if not user_id == self.env.uid:
        #             raise Warning(
        #                 _("You should have access for edit this "
        #                   "lead/opportunity."))
        #         return super(CrmLead, self).write(vals)


class CrmLead2opportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.model
    def default_get(self, fields_list):
        res = super(CrmLead2opportunityPartner, self).default_get(fields_list)
        if self._context:
            if self._context.get('default_client_type'):
                if self._context.get('default_client_type') == 'existing':
                    res.update({'action': 'exist'})
                elif self._context.get('default_client_type') == 'prospect':
                    res.update({'action': 'create'})
                else:
                    res.update({'action': 'nothing'})
        return res

