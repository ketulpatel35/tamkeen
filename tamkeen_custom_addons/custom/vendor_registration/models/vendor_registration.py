from openerp import models, api, fields, _, tools
from datetime import date, datetime
from odoo.exceptions import Warning
import re
import time
from odoo.exceptions import Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


class VendorRegistration(models.Model):
    _name = 'vendor.registration'
    _description = "Vendor Registration"
    _inherit = ['mail.thread']

    STATES = [
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('evaluation', 'Evaluation'),
        ('vendor_registered', 'Vendor Registered'),
        ('blacklist', 'Blacklisted'),
        ('cancel', 'Cancelled')
    ]

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(string="Image", attachment=True,
                          help="This field holds the image used as avatar "
                               "for this contact, limited to 1024x1024px")
    name = fields.Char(string='Name')
    company_type = fields.Selection([('person', 'Individual'),
                                     ('company', 'Company')],
                                    default='company', string='Company Type')
    is_company = fields.Boolean(string='Is a Company', default=False,
                                help="Check if the contact is a company, "
                                     "otherwise it is a person")
    color = fields.Integer(string='Color Index', default=0)
    state = fields.Selection(STATES, string='Application Status', copy=False)
    website = fields.Char(help="Website of Partner or Company")

    contractor = fields.Boolean(string='Contractor')
    consultant = fields.Boolean(string='Consultant')
    other_service = fields.Boolean(string='Other Service')
    other_service_note = fields.Char(string='Specify Other Service')
    title = fields.Many2one('res.partner.title', string='Title')
    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice address'),
         ('delivery', 'Shipping address'),
         ('other', 'Other address')], string='Address Type',
        default='contact',
        help="Used to select automatically the right address according to "
             "the context in sales and purchases documents.")
    comment = fields.Text(string='Notes')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(change_default=True)
    city = fields.Char(string='City')
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country',
                                 ondelete='restrict')
    phone = fields.Char(string='Phone')
    fax = fields.Char(string='Fax')
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    arabic_name = fields.Char('Arabic Nam')
    national = fields.Selection([
        ('saudi_national', '100% Owned by a Saudi National'),
        ('foreign_investment', 'Non-Saudi National'),
        ('other', 'Other')], string='National')
    ownership_other_note = fields.Char('Please specify')
    owner_partner_ids = fields.One2many('ownership.partner',
                                        'vendor_registration_id',
                                        string='Owner/Partner')
    financial_statement_information_ids = fields.One2many(
        'financial.statement.information', 'vendor_registration_id',
        string='Financial Statement Information')
    required_document_ids = fields.One2many('required.document.procurement',
                                            'vendor_registration_id',
                                            string='Required Document')
    plant_facilities_ids = fields.One2many('plant.other.facilities',
                                           'vendor_registration_id',
                                           string='Plan & Other Facilities')
    equipment_machinary_ids = fields.One2many('equipment.machinery',
                                              'vendor_registration_id',
                                              string='Equipment & Machinery')
    quality_hse_ids = fields.One2many('quality.hse.conf',
                                      'vendor_registration_id',
                                      string='Quality & HSE')
    company_declaration = fields.Text(string='Company Declaration')
    active = fields.Boolean(string='Active', default=True)
    # force "active_test" domain to bypass _search() override
    parent_id = fields.Many2one('vendor.registration')
    child_ids = fields.One2many('vendor.registration', 'parent_id',
                                string='Contacts')
    category = fields.Selection([('general', 'General'),
                                 ('others', 'Others')], default='general',
                                string='Category')
    survey_template_id = fields.Many2one('survey.survey', string='Template')
    number_of_employees = fields.Char('Number of Employees')
    notes = fields.Text(string='Notes', copy=False)
    is_black_list = fields.Boolean('Black List?', default=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Releted Vendor('
                                                       'Partner)', copy=False)
    is_vendor = fields.Boolean('is vendor', copy=False)
    vendor_activities_ids = fields.Many2many('vendor.activities',
                                             'rel_vendor_regs_activities',
                                             'reg_id', 'act_id', 'Activities')
    reviewd_user_id = fields.Many2one('res.users', string='Reviewed By',
                                      readonly=True, copy=False)
    review_date = fields.Datetime(string='Review Date',
                                  readonly=True, copy=False)
    evaluated_user_id = fields.Many2one('res.users', string='Evaluated By',
                                        readonly=True, copy=False)
    evaluated_date = fields.Datetime(string='Evaluation Date',
                                     readonly=True, copy=False)
    registered_user_id = fields.Many2one('res.users', string='Registered By',
                                         readonly=True, copy=False)
    registered_date = fields.Datetime(string='Registertion Date',
                                      readonly=True, copy=False)
    reset_reason = fields.Text('Reason', readonly=True, copy=False)
    reset_date = fields.Datetime(string='Return Date',
                                 readonly=True, copy=False)
    reset_user_id = fields.Many2one('res.users', string='Returned By',
                                    readonly=True, copy=False)
    stage_logs = fields.One2many('vendor.register.stage.logs',
                                 'vendor_id', 'Stage Logs',
                                 readonly=True)
    code = fields.Char('Code', copy=False)
    vendor_categorized = fields.Selection([
        ('Micro', 'Micro'), ('Small', 'Small'), ('Medium', 'Medium'),
        ('Large', 'Large')], string='Vendor Categorization')
    # Accounting information
    accounting_information_ids = fields.One2many(
        'accounting.information', 'vendor_reg_id', 'Accounting Information')
    commercial_registration = fields.Char('Commercial Registration#')
    commercial_registration_expiry_date = fields.Date(
        'Commercial Registration Expiry Date')

    @api.model
    def _get_sequence(self):
        seq = self.env['ir.sequence'].next_by_code('vendor.registration')
        return seq

    @api.model
    def create(self, vals):
        """
        :return:
        """

        if vals:
            vals['code'] = self._get_sequence()
            res = super(VendorRegistration, self).create(vals)

            return res

    @api.multi
    def write(self, vals):
        if not self._context.get('state_black_list'):
            if vals.get('state'):
                if self.stage_logs:
                    stage_log_rec = self.stage_logs[-1]
                    if stage_log_rec.stage == 'blacklist':
                        raise Warning(_("You are not allowed to change the "
                                        "vendor status from the kanban view "
                                        "!"))
                if vals.get('state') == 'blacklist':
                    raise Warning(_("You are not allowed to change the "
                                    "vendor status from the kanban view "
                                    "!"))
        for rec in self:
            # when record come to review state
            if vals.get('state') == 'review':
                rec.add_stage_log(vals)
                if not rec.env.user.has_group(
                        'vendor_registration.group_vendor_management_can_review'):
                    raise Warning(_("You don't have the access to change the "
                                    "status to: %s.") % vals.get('state'))
            # when record come to evaluation state
            if vals.get('state') == 'evaluation':
                rec.add_stage_log(vals)
                # rec.evaluated_user_id = rec.env.user.id
                # rec.evaluated_date = datetime.now().strftime(OE_DTFORMAT)
                if not rec.env.user.has_group(
                        'vendor_registration.'
                        'group_vendor_management_can_evaluated'):
                    raise Warning(_("You don't have the access to change the "
                                    "status to: %s.") % vals.get('state'))
            # when record come to vendor_registered state
            if vals.get('state') == 'vendor_registered':
                rec.add_stage_log(vals)
                if not rec.env.user.has_group(
                        'vendor_registration.group_vendor_management_can_register'):
                    raise Warning(_("You don't have the access to change the "
                                    "status to: %s.") % vals.get('state'))
            # when record come to blacklist state
            if vals.get('state') == 'blacklist':
                rec.add_stage_log(vals)
                if not rec.env.user.has_group(
                        'vendor_registration.group_manage_vendor'):
                    raise Warning(_("You don't have the access to change the "
                                    "status to: %s.") % vals.get('state'))
            # when record come to draft state
            if vals.get('state') == 'draft':
                rec.add_stage_log(vals)
                if not rec.env.user.has_group(
                        'vendor_registration.group_vendor_return_to_draft'):
                    raise Warning(_("You don't have the access to change the "
                                    "status to: %s.") % vals.get('state'))
            # when record come to cancel state
            if vals.get('state') == 'cancel':
                # Add Stage log
                rec.add_stage_log(vals)
                if not rec.env.user.has_group(
                        'vendor_registration.group_vendor_cancel'):
                    raise Warning(_("You don't have the access to change the "
                                    "status to: %s.") % vals.get('state'))
            return super(VendorRegistration, rec).write(vals)

    def add_stage_log(self, vals):
        # Add Stage log
        stage_log_obj = self.env['vendor.register.stage.logs']
        today = datetime.strptime(time.strftime(OE_DTFORMAT), OE_DTFORMAT)

        if self.stage_logs:
            start_today = datetime.strptime(self.stage_logs[
                                                -1].date_from, OE_DTFORMAT)
            end_today = today
            log_duration = end_today - start_today
            stage_log_rec = stage_log_obj.browse(
                self.stage_logs[-1].id)
            stage_log_rec.write({'vendor_id': self.id,
                                 'date_to': end_today,
                                 'duration': log_duration.days})

        stage_log_obj.create({'vendor_id': self.id,
                              'stage': vals.get('state'),
                              'user_id': self._uid,
                              'date_from': today})

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=False):
        """
        Override read_group to always display all states.
        :return:
        """
        if groupby and groupby[0] == "state":
            # Default result structure
            states = self.STATES
            read_group_all_states = [{
                '__domain': domain,
                'state': state_value,
                'state_count': 0,
            } for state_value, state_name in states]
            # Get standard results
            read_group_res = super(VendorRegistration, self).read_group(
                domain, fields, groupby, offset=offset, limit=limit,
                orderby=orderby, lazy=lazy)
            # Update standard results with default results
            result = []
            for state_value, state_name in states:
                res = filter(lambda x: x['state'][0] == state_value,
                             read_group_res)
                if not res:
                    res = filter(lambda x: x['state'] == state_value,
                                 read_group_all_states)
                    res[0]['__fold'] = True
                res[0]['state'] = [state_value, state_name]
                result.append(res[0])
            return result
        else:
            return super(VendorRegistration, self).read_group(
                domain, fields, groupby, offset=offset, limit=limit,
                orderby=orderby, lazy=lazy)

    @api.one
    @api.constrains('owner_partner_ids')
    def check_owner_partner(self):
        if self.owner_partner_ids:
            owner_parsentage = 0
            for owner_partner_rec in self.owner_partner_ids:
                owner_parsentage += owner_partner_rec.ownership
            if owner_parsentage > 100:
                raise Warning(_('Warning !\n partner ownership should be in '
                                'between 1% to 100% !'))

    # @api.one
    # @api.constrains('email')
    # def check_email_validation(self):
    #     """
    #     check email format
    #     :return:
    #     """
    #     if self.email:
    #         match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.['
    #                          'a-z0-9-]+)*(\.[a-z]{2,4})$', self.email)
    #         if not match:
    #             raise Warning(_('Please enter a valid Email ID.'))

    @api.multi
    def set_active_inactive(self):
        view = self.env.ref(
            'vendor_registration.blacklist_vendor_form_view')
        if not view:
            return True
        return {
            'name': _('Blacklisted Reason'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'blacklist.vendor',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.onchange('category')
    def onchange_category(self):
        if self.category:
            template_rec = self.env['procrument.template']. \
                search([('category', '=', self.category)], limit=1)
            if template_rec and template_rec.survey_template_id:
                self.survey_template_id = template_rec.survey_template_id.id

    @api.multi
    def open_survey_template(self):
        res = [self.survey_template_id.id]
        if res:
            return {
                'name': _('Survey Template'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'survey.survey',
                'domain': [('id', 'in', res)],
            }

    @api.model
    def _read_group_fill_results(self, domain, groupby,
                                 remaining_groupbys, aggregated_fields,
                                 count_field, read_group_result,
                                 read_group_order=None):
        """
        The method seems to support grouping using m2o fields only,
        while we want to group by a simple status field.
        Hence the code below - it replaces simple status values
        with (value, name) tuples.
        """
        if groupby == 'state':
            STATES_DICT = dict(self.STATES)
            for result in read_group_result:
                state = result['state']
                result['state'] = (state, STATES_DICT.get(state))

        return super(VendorRegistration, self)._read_group_fill_results(
            domain, groupby, remaining_groupbys, aggregated_fields,
            count_field, read_group_result, read_group_order
        )

    @api.multi
    def confirm_vendor(self):
        """
        move record to vendor review state .
        :return:
        """
        for rec in self:
            rec.state = 'review'

    @api.multi
    def vendor_evaluation(self):
        """
        move record to vendor evaluation state.
        :return:
        """
        for rec in self:
            rec.state = 'evaluation'
            rec.reviewd_user_id = self.env.user.id
            rec.review_date = datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def vendor_registered(self):
        """
        move record to vendor vendor_registered state.
        :return:
        """
        for rec in self:
            rec.state = 'vendor_registered'
            rec.registered_user_id = self.env.user.id
            rec.registered_date = datetime.now().strftime(OE_DTFORMAT)

    @api.one
    def get_vendor_data_dict(self, parent_rec=False):
        """
        :return:
        """
        country_id = self.country_id
        parent_rec = parent_rec
        if parent_rec:
            if not country_id:
                country_id = parent_rec.country_id
        company_type = self.company_type
        is_company = True
        if self._context and self._context.get('company_type'):
            company_type = self._context.get('company_type')
            is_company = False
        data_values = {
            'supplier': True,
            'customer': False,
            'company_type': company_type,
            'parent_id': parent_rec.id if parent_rec else False,
            'name': self.name,
            'is_company': is_company,
            'image': self.image,
            'type': self.type,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state_id': self.state_id.id if self.state_id else False,
            'zip': self.zip,
            'country_id': country_id.id if country_id else False,
            'website': self.website,
            'phone': self.phone,
            'mobile': self.mobile,
            'fax': self.fax,
            'email': self.email,
            'title': self.title.id if self.title else False,
            'active': True,
            'commercial_registration': self.commercial_registration,
            'commercial_registration_expiry_date':
                self.commercial_registration_expiry_date,
            'vendor_reg_id': self.id,
        }
        return data_values

    @api.constrains('email')
    def _check_validation_for_vendor(self):
        if self.email:
            vendor_rec = self.env['vendor.registration'].search([
                ('email', '=', self.email),
                ('state', 'in', ['draft',
                                 'review',
                                 'evaluation',
                                 'vendor_registered', 'blacklist']),
                ('id', '!=', self.id)])
            if vendor_rec:
                raise ValidationError(_('Already there is a partner'
                                        'with the same '
                                        'Email ID %s') % self.email)
        return True

    @api.model
    def _check_validation(self, data_values):
        """
        check validation on cata before create partners
        :param data_values:
        :return:
        """
        if data_values:
            if data_values.get('email'):
                partner_rec = self.env['res.partner'].search([
                    ('email', '=', data_values.get('email'))])
                if partner_rec:
                    raise Warning(_('Already there is a partner with '
                                    'the same '
                                    'Email ID %s') % (
                                      data_values.get('email')))
            return True

    @api.multi
    def vendor_creation(self):
        """
        create vendor.
        :return:
        """
        context = dict(self._context)
        for rec in self:
            if rec.partner_id:
                raise Warning(_('Vendor Already Created. !'))
            data_values = rec.get_vendor_data_dict(False)[0]
            self._check_validation(data_values)
            partner_rec = self.env['res.partner'].create(data_values)
            rec.partner_id = partner_rec.id
            rec.is_vendor = True
            # vendor parent child relationship
            for child_rec in rec.child_ids:
                ctx = {'company_type': 'person'}
                data_values = child_rec.with_context(ctx).get_vendor_data_dict(
                    partner_rec)[0]
                self._check_validation(data_values)
                child_partner_rec = self.env['res.partner'].create(data_values)
                child_rec.partner_id = child_partner_rec.id

    @api.multi
    def cancel_vendor(self):
        """
        for cancel Vendor
        :return:
        """
        for rec in self:
            rec.state = 'cancel'

    @api.multi
    def reset_to_draft(self):
        view = self.env.ref(
            'vendor_registration.vendor_reset_form_view')
        if not view:
            return True
        context = dict(self._context)
        context.update({'vendor_id': self.id})
        return {
            'name': _('Blacklisted Reason'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vendor.registration.reset',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    @tools.ormcache('self._uid')
    def context_get(self):
        user = self.env.user
        result = {}
        for k in self._fields:
            if k.startswith('context_'):
                context_key = k[8:]
            elif k in ['lang', 'tz']:
                context_key = k
            else:
                context_key = False
            if context_key:
                res = getattr(user, k) or False
                if isinstance(res, models.BaseModel):
                    res = res.id
                result[context_key] = res or False
        return result


class OwnershipPartner(models.Model):
    _name = 'ownership.partner'

    name_owner_id = fields.Many2one('res.partner', string='Owner Name')
    country_id = fields.Many2one('res.country', string='Nationality')
    ownership = fields.Float(string='Ownership %')
    vendor_registration_id = fields.Many2one('vendor.registration',
                                             string='Vendor Registration')

    @api.onchange('name_owner_id')
    def onchange_owner_id(self):
        if self.name_owner_id and self.name_owner_id.country_id:
            self.country_id = self.name_owner_id.country_id

    @api.one
    @api.constrains('ownership')
    def check_ownership(self):
        if self.ownership and self.ownership > 100 or self.ownership < 1:
            raise Warning(_('Warning !\n partner ownership should be in '
                            'between 1% to 100% !'))


class FinancialStatementInformation(models.Model):
    _name = 'financial.statement.information'

    @api.model
    def get_current_year(self):
        """
        return current year
        :return:
        """
        return date.today().year

    @api.model
    def get_expect_years(self):
        year_list = []
        current_year = self.get_current_year()
        start_year = 1990
        end_year = current_year + 5
        for y in range(start_year, end_year):
            year = str(y)
            year_list.append((year, year))
        return year_list

    year = fields.Selection(get_expect_years, string='Statement Year')
    revenue = fields.Char(string='Revenue')
    number_of_project = fields.Char('Number of Projects')
    vendor_registration_id = fields.Many2one('vendor.registration',
                                             string='Vendor Registration')
    financial_statement_config_id = fields.Many2one(
        'financial.statement.configuration', string='Financial Statement')
    financial_document = fields.Binary(string='Document/s')
    doc_name = fields.Char('File name')


class PlantOtherFacilities(models.Model):
    _name = 'plant.other.facilities'

    serial_no = fields.Char(string='Serial Number')
    plant_description = fields.Char(string='Plant Description')
    main_activity = fields.Char(string='Main Activity')
    vendor_registration_id = fields.Many2one('vendor.registration',
                                             string='Vendor Registration')
    location = fields.Char(string='Location')
    area_m2 = fields.Float(string='Area (m2)')


class EquipmentMachinery(models.Model):
    _name = 'equipment.machinery'

    serial_no = fields.Char(string='Serial Number')
    desc_equip_machinery = fields.Char(
        string='Description of Equipment/Machinery')
    capacity_size = fields.Char(string='Capacity/Size')
    model_year = fields.Integer(string='Model Year')
    quantity = fields.Float(string='Quantity')
    vendor_registration_id = fields.Many2one('vendor.registration',
                                             string='Vendor Registration')


class DualityHseConf(models.Model):
    _name = 'quality.hse.conf'

    serial_no = fields.Char(string='Serial Number')
    quality_hse_id = fields.Many2one('quality.hse', 'Quality & HSE')
    quality_yes = fields.Boolean(string='Yes')
    quality_no = fields.Boolean(string='No')
    vendor_registration_id = fields.Many2one(
        'vendor.registration', 'Vendor Registration')

    @api.onchange('quality_yes')
    def onchange_quality_yes(self):
        if self.quality_yes is True:
            self.quality_no = False

    @api.onchange('quality_no')
    def onchange_quality_no(self):
        if self.quality_no is True:
            self.quality_yes = False


class RequiredDocumentProcurement(models.Model):
    _name = 'required.document.procurement'

    serial_no = fields.Integer(string='Serial Number', default=1)
    date = fields.Date(string='Issue Date')
    expiration_date = fields.Date(string = "Expiration Date")
    document_certificate = fields.Many2one('document.certificate.attachment',
                                           string='Document/Certificate')
    attachment_status = fields.Selection([('required', 'Required'),
                                          ('not_required', 'Not Required')],
                                         string='Attachment Status')
    attached_na = fields.Boolean(string='N/A')
    vendor_registration_id = fields.Many2one('vendor.registration',
                                             string='Vendor Registration')
    attachment = fields.Binary(string='Attachment')
    attachment_name = fields.Char('File Name')


class VendorRegistrationLogs(models.Model):
    _name = 'vendor.register.stage.logs'

    vendor_id = fields.Many2one('vendor.registration', 'Applicant',
                                required=True, readonly=True,
                                ondelete="cascade")
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('evaluation', 'Evaluation'),
        # ('hold', 'Hold'),
        # ('short_listed', 'Short Listed'),
        ('vendor_registered', 'Vendor Registered'),
        ('blacklist', 'Blacklisted'),
        ('cancel', 'Cancelled')
    ], string='Application Status', required=True)
    user_id = fields.Many2one('res.users', 'By')
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    duration = fields.Float('Duration(Days)')