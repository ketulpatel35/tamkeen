from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit = 'project.project'

    @api.depends('milestones_schedule_ids')
    def get_invoiced_value(self):
        invoiced = 0.0
        for rec in self:
            for line in rec.milestones_schedule_ids:
                if line.invoiced_value:
                    invoiced += line.invoiced_value
            rec.invoiced_values = invoiced

    @api.depends('milestones_schedule_ids')
    def get_collected_value(self):
        collected = 0.0
        for rec in self:
            for line in rec.milestones_schedule_ids:
                if line.collected_payment:
                    collected += line.collected_payment
            rec.collected_values = collected

    @api.depends('milestones_schedule_ids')
    def get_remaining_value(self):
        collected = 0.0
        total = 0.0
        for rec in self:
            for line in rec.milestones_schedule_ids:
                if line.collected_payment:
                    total += line.estimated_value
                    collected += line.collected_payment
            rec.remaining_values = total - collected

    @api.depends('milestones_schedule_ids')
    def _compute_milestones_count(self):
        for project in self:
            project.milestones_count = len(project.milestones_schedule_ids)

    @api.depends('milestones_schedule_ids.estimated_value',
                 'milestones_schedule_ids.estimated_percentage',
                 'milestones_schedule_ids')
    def compute_total_milestones_value(self):
        """
        compute total milestones value
        :return:
        """
        for rec in self:
            total_milestones_value = 0.0
            total_estimated_percentage = 0.0
            for line_rec in rec.milestones_schedule_ids:
                total_milestones_value += line_rec.estimated_value
                total_estimated_percentage += line_rec.estimated_percentage
            rec.total_milestones_value = total_milestones_value
            rec.total_estimated_percentage = total_estimated_percentage

    @api.depends('milestones_schedule_ids.estimated_percentage')
    def calculate_avg_progress_percentages(self):
        for rec in self:
            total_milestones_percentage = 0.0
            count = 0
            for milestonerec in rec.milestones_schedule_ids:
                total_milestones_percentage += \
                    milestonerec.estimated_percentage
                count += 1
            if total_milestones_percentage and count:
                rec.avg_progress_percentage = \
                    total_milestones_percentage / count

    @api.multi
    def get_vendor_data(self):
        result = {}
        for rec in self:
            for mile in self.env['project.milestones.schedule'].search([('project_id', '=', rec.id)]):
                if mile.partner_id:
                    if str(mile.partner_id) not in result.keys():
                        result.update({str(mile.partner_id):
                            [str(mile.partner_id.name),
                             mile.vendor_contract_value, mile.collected_payment]})
                    else:
                        name = result.get(str(mile.partner_id))[0]
                        total = result.get(str(mile.partner_id))[1] +\
                                mile.vendor_contract_value
                        collected = result.get(str(mile.partner_id))[2] +\
                        mile.collected_payment
                        result.update({str(mile.partner_id): [name, total,
                                                              collected]})
        return result

    @api.depends('milestones_schedule_ids')
    def compute_vendor_values(self):
        for project in self:
            paid_amount = 0.0
            contract_amount = 0.0
            for milestone in project.milestones_schedule_ids:
                paid_amount += milestone.collected_payment
                contract_amount += milestone.vendor_contract_value
            project.vendor_paid_value = paid_amount
            project.vendor_remaining_value = contract_amount - paid_amount

    milestones_schedule_ids = fields.One2many('project.milestones.schedule',
                                              'project_id',
                                              string='Delivery Details')
    avg_progress_percentage = fields.Float(
        'Avg Progress Percentage', compute=calculate_avg_progress_percentages,
        store=True)
    total_milestones_value = fields.Float(
        'Total Milestones Value', store=True,
        compute='compute_total_milestones_value')

    total_estimated_percentage = fields.Float(
        'Total Milestones Percentage', store=True,
        compute='compute_total_milestones_value')
    milestones_count = fields.Integer(compute='_compute_milestones_count',
                                      string="Milestones")
    invoiced_values = fields.Float('Invoiced Value (SAR)',
                                   compute=get_invoiced_value)
    collected_values = fields.Float('Collected Payments (SAR)',
                                    compute=get_collected_value)
    remaining_values = fields.Float('Remaining Payments (SAR)',
                                    compute=get_remaining_value)
    vendor_paid_value = fields.Float(
        string='Total Paid Value(Vendor)', compute=compute_vendor_values)
    vendor_remaining_value = fields.Float(
        string='Remaining Value(Vendor)', compute=compute_vendor_values)
