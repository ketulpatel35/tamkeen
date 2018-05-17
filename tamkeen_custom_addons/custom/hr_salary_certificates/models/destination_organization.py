# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DestinationOrganization(models.Model):
    _name = "destination.organization"
    _order = 'sequence'

    _sql_constraints = [('destination_organization_code_unique',
                         'unique(code)',
                         'The code for the destination organization must be '
                         'unique per company !')]

    name = fields.Char('Name', copy=False)
    arabic_name = fields.Char('Arabic Name')
    code = fields.Char('Code', copy=False)
    dest_org_type = fields.Many2one('destination.organization.type',
                                    string='Destination Organization Type',
                                    copy=False)
    active = fields.Boolean('Active', copy=False, default=True)
    sequence = fields.Integer('Sequence', copy=False)


class DestinationOrganizationType(models.Model):
    _name = "destination.organization.type"
    _order = 'sequence'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _sql_constraints = [('destination_organization_type_code_unique',
                         'unique(code)',
                         'The code for the destination organization must be '
                         'unique per company !')]

    sequence = fields.Integer('Sequence', copy=False)
    name = fields.Char('Name', copy=False, track_visibility='onchange')
    arabic_name = fields.Char('Arabic Name')
    code = fields.Char('Code', copy=False, track_visibility='onchange')
    is_bank = fields.Boolean('Is Bank', copy=False,
                             track_visibility='onchange')
    active = fields.Boolean('Active', copy=False, default=True)
    purpose_required = fields.Boolean(string='Purpose Required')
    purpose_ids = fields.Many2many('destination.org.purpose',
                                   'rel_dest_type_purpose',
                                   'type_id', 'purpose_id', 'Purpose',
                                   copy=False)
    max_report_print = fields.Integer('Maximum Report Printing', default=5)
    contact_email = fields.Char('Contact Email')
    employee_id = fields.Many2one('hr.employee', string='Authorised Official')
