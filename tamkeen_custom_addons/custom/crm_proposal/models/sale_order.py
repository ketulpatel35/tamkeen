from odoo import models, api, fields
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.depends('milestones_schedule_ids')
    def _compute_total_percentage(self):
        """
        Compute total percentage
        :return:
        """
        for rec in self:
            percentage = 0.00
            for po_deli_rec in rec.milestones_schedule_ids:
                percentage += po_deli_rec.percentage

            rec.total_percentage = percentage

    # assignment_date = fields.Date(string='Assignment Date')
    # planned_start_date = fields.Date(string='Planned Start Date')
    # proposal_writing_duration = fields.Float(
    #     string='Planned Proposal Writing Duration')
    # planned_review_duration = fields.Float(string='Planned Review Duration')
    # planned_release_date = fields.Date(string='Planned Release '
    #                                           'Date')
    # actual_start_date = fields.Date(string='Actual Start Date')
    # actual_release_date = fields.Date(string='Actual Release Date')
    # total_proposal_value = fields.Float(string='Total Proposal Value')
    # proposal_status = fields.Selection([('new', 'New'), ('writing',
    #                                                      'Writing'),
    #                                     ('submitted', 'Submitted'),
    #                                     ('re_submitted', 'Re-Submitted')])
    #Terms and condition
    term_condition = fields.Text(string='Terms & Condition')
    #Bid
    # submission_date = fields.Date(string='Submission Date')
    # bid_status = fields.Selection([('new', 'New'), ('bids', 'Bids'),
    #                                ('submitted', 'Submitted'),
    #                                ('evaluated', 'Evaluated'), ('win', 'Win'),
    #                                ('loss', 'Loss'), ('cancelled',
    #                                                   'Cancelled')],
    #                               string='Bid Status')
    # financial_proposal_ranking = fields.Integer(string='Financial Proposal '
    #                                                    'Ranking')
    # guarantee_issue = fields.Selection([('yes', 'Yes'), ('no', 'No')],
    #                                      string='Guarantee Issue')
    # saudi_certificate = fields.Selection([('yes', 'Yes'), ('no', 'No')],
    #                                      string='Saudization Certificate')
    # bid_notes = fields.Text(string='Bid Notes')
    # bid_questions = fields.Text(string='Bid Questions')
    milestones_schedule_ids = fields.One2many('crm.milestones.schedule',
                                              'sale_order_id',
                                              'Delivery Details')
    total_percentage = fields.Float(compute='_compute_total_percentage',
                                    string='Total Percentage', store=True)
    # attachment_ids = fields.One2many('crm.attachment', 'sale_id',
    #                                  string='Attachment/s')

