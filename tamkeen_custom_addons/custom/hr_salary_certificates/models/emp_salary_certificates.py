# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, modules, tools
from datetime import datetime
from odoo.exceptions import Warning
from odoo.exceptions import UserError


class EmpSalaryCertificates(models.Model):
    _name = "emp.salary.certificates"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Employment Certificate'

    name = fields.Char('Reference', copy=False, translate=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Name',
                                  default=lambda self:
                                  self.env['hr.employee'].search([
                                      ('user_id', '=', self._uid)],limit=1)
                                  or False, copy=False,
                                  track_visibility='onchange')
    country_id = fields.Many2one('res.country',
                                 related='employee_id.country_id',
                                 string='Nationality', copy=False)
    current_country_code = fields.Char(related='country_id.code',
                                       string='Country Code', copy=False)
    identification_number = fields.Char('Identification Number',
                                        related='employee_id.identification_id', copy=False)
    iqama_number = fields.Char(string='Iqama Number',
                               related='employee_id.iqama_number', copy=False)
    employee_company_id = fields.Char(string='Employee Company ID',
                                      related='employee_id.f_employee_no',
                                      copy=False)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id',
                             string='Position', copy=False)
    date_of_joining = fields.Date(string='Date of Joining',
                                  related='employee_id.initial_employment_date', copy=False)
    state = fields.Selection([('draft', 'Draft'),
                              ('hr_approval', 'HR Approval'),
                              ('ready_for_printing', 'Ready For Printing'),
                              ('reject', 'Reject')],
                             default='draft', copy=False,
                             track_visibility='onchange')
    is_passport_number = fields.Boolean(string='Passport Number', copy=False)
    destination_organization_type = fields.Many2one(
        'destination.organization.type', copy=False,
        string='Destination Organization Type')
    is_bank = fields.Boolean('Is Bank',
                             related='destination_organization_type.is_bank',
                             copy=False)
    bank_id = fields.Many2one('res.bank', 'Bank', copy=False,
                              track_visibility='onchange')
    destination_organization_id = fields.Many2one(
        'destination.organization', string='Destination Organization', copy=False)
    dest_org_purpose_id = fields.Many2one('destination.org.purpose',
                                          'Purpose', copy=False,
                                          track_visibility='onchange')
    need_to_add_missing_destination = fields.Boolean(
        string='Need to add Missing Destination', copy=False,
        track_visibility='onchange')
    other_dest_org = fields.Char('Other Destination Organization',
                                 copy=False, track_visibility='onchange')
    need_to_add_missing_purpose = fields.Boolean('Need to add Missing '
                                                 'Purpose', copy=False,
                                                 track_visibility='onchange')
    other_purpose = fields.Char('Other Purpose', copy=False,
                                track_visibility='onchange')

    certificate_notarized_chamber_of_commerce = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')],
        string='Would you like to have your certificate authenticated by chamber '
               'of commerce?', default='no', copy=False,
        track_visibility='onchange')
    hr_dept_to_notarize = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')], copy=False,
        string='Would you like HR Dapartment to authenticate it for you?',
        default='no', track_visibility='onchange')
    deduct_fee_from_monthly_salary = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')], copy=False,
        string = 'Deduct fees from my monthly salary?', default='no',
        track_visibility='onchange')
    emp_salary_rule_ids = fields.Many2many(
        'hr.salary.rule', 'rel_e_salary_rule_certificates',
        'c_id', 'r_id', 'Employment Certificate', copy=False,
        track_visibility='onchange')
    payslip_amendment_id = fields.Many2one('hr.payslip.amendment',
                                           string='Payship Amendment',
                                           copy=False,
                                           track_visibility='onchange')
    service_log_ids = fields.One2many('salary.certificates.service.log',
                                      'salary_certificates_id',
                                      string='Service Log', copy=False,
                                      track_visibility='onchange')
    max_report_print = fields.Integer('Maximum Printing Count Per Request', default=1, copy=False)
    purpose_required = fields.Boolean(string='Purpose Required',
                                      related='destination_organization_type.purpose_required', store=True)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
        set employee related data
        :return:
        """
        if self.employee_id:
            self.emp_salary_rule_ids = False

    @api.onchange('destination_organization_type')
    def onchange_destination_organization_type(self):
        """
        purpose based on selected org type
        :return:
        """
        self.dest_org_purpose_id = False
        self.destination_organization_id = False
        self.bank_id = False
        self.other_purpose = False
        self.other_dest_org = False
        self.need_to_add_missing_destination = False
        self.need_to_add_missing_purpose = False
        res = {}
        purpose_ids = []
        if self.destination_organization_type:
            purpose_ids = self.destination_organization_type.purpose_ids.ids
        res.update({'dest_org_purpose_id': [('id', 'in', purpose_ids)]})
        return {'domain': res}

    @api.onchange('need_to_add_missing_destination',
                  'need_to_add_missing_purpose')
    def onchange_add_missing_bool(self):
        """
        :return:
        """
        if self.need_to_add_missing_destination:
            self.bank_id = False
            self.destination_organization_id = False
        if self.need_to_add_missing_purpose:
            self.dest_org_purpose_id = False

    @api.onchange('certificate_notarized_chamber_of_commerce',
                  'hr_dept_to_notarize')
    def onchange_questions(self):
        if self.certificate_notarized_chamber_of_commerce == 'no':
            self.hr_dept_to_notarize = 'no'
        if self.hr_dept_to_notarize:
            self.deduct_fee_from_monthly_salary = 'no'

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'emp.salary.certificates')
        return super(EmpSalaryCertificates, self).create(vals)

    @api.multi
    def confirm_salary_certificates(self):
        """
        confirm salary certificates
        :return:
        """
        for rec in self:
            if rec.need_to_add_missing_destination or rec.need_to_add_missing_purpose:
                rec.send_notification_mail_to('hr_approval')
                rec.state = 'hr_approval'
            else:
                if rec.destination_organization_type.is_bank and not rec.bank_id:
                    raise Warning(
                        "You are not allowed to print a report without defining the destination bank.")
                elif not rec.destination_organization_type.is_bank and not rec.destination_organization_id:
                    raise Warning(
                        "You are not allowed to print a report without defining the destination organization.")
                else:
                    # For the validation purpose the HR need to recieve any printing request, later it will be as per the policy.
                    rec.send_notification_mail_to('hr_approval')
                    rec.state = 'hr_approval'
                    # self.send_notification_mail_to('confirm')
                    # rec.state = 'ready_for_printing'

    @api.multi
    def _check_group(self, group_xml_id):
        users_obj = self.env['res.users']
        if users_obj.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def copy(self, default=None):
        if not self._check_group(
                'hr_salary_certificates.group_certificate_on_behalf_approval_srvs'
        ):
            for rec in self:
                if rec.employee_id.user_id.id != self._uid:
                    raise Warning(_(
                        "You don't have the permissions to make such changes."
                    ))
        return super(EmpSalaryCertificates, self).copy(default=default)

    @api.multi
    def unlink(self):
        """
        can not delete record which is in open or done
        :return:
        """
        for rec in self:
            if rec.state not in ['draft']:
                raise Warning("You can delete only the requests in draft "
                              "state.")
        return super(EmpSalaryCertificates, self).unlink()

    @api.multi
    def hr_approve_salary_certificates(self):
        """
        hr approved salary certificates
        :return:
        """
        for rec in self:
            rec.state = 'ready_for_printing'
            rec.send_notification_mail_to('ready_for_printing')

    @api.multi
    def check_update_max_report_print(self):
        """
        check for Report Printing Validation
        :return:
        """
        max_report_print = 5
        if self.destination_organization_type and \
                self.destination_organization_type.max_report_print:
            max_report_print = \
                self.destination_organization_type.max_report_print
        if self.max_report_print > max_report_print:
            raise Warning(_('You printed this report as per the company '
                            'printing times policy, For more kindly contact '
                            'the HR team.'))
        self.max_report_print += 1

    @api.multi
    def hr_reject_salary_certificates(self):
        """
        hr reject or set to draft salary certificate
        :return:
        """
        message = 'Reset to Draft Employment Certificate'
        context = self._context.copy()
        if self._context.get('is_reject'):
            message = 'Reject Employment Certificate'
            context.update({'default_is_reject': True})
        view = self.env.ref(
            'hr_salary_certificates.certificates_reject_reason_form_view')

        return {
            'name': _(message),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'certificates.reject.reason',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def send_notification_mail_to(self, token):
        """
        :param token:
        :return:
        """
        context = dict(self._context)
        template_xml_ref = ''
        rec_id = self.id
        email_to = ''
        # if token == 'confirm':
        #     template_xml_ref = 'emp_salary_certificates_confirm'
        if token == 'hr_approval':
            template_xml_ref = 'emp_salary_certificates_hr_approval'
        elif token == 'rejected':
            template_xml_ref = 'emp_salary_certificates_rejected'
        elif token == 'return':
            template_xml_ref = 'emp_salary_certificates_return'
        elif token == 'ready_for_printing':
            template_xml_ref = 'emp_salary_certificates_ready_to_print'
        if template_xml_ref:
            self.with_context(context)._send_email(template_xml_ref,
                                                    email_to,
                                                   token,
                                             rec_id)

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state):
        window_action_id = False
        if dest_state != 'hr_approval':
            window_action_ref = \
                'hr_salary_certificates.emp_salary_certificates_action'
        else:
            window_action_ref = \
                'hr_salary_certificates.emp_salary_certificates_action_pending_hr_approvals'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    @api.multi
    def _send_email(self, template_xml_ref, email_to, token, rec_id):
        """
        send email notification
        :param template_xml_ref: xml temp id
        :param email_to: email to
        :param rec_id: record id
        :return:
        """
        context = self._context or None
        display_link = False
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url.static')
        if template_xml_ref:
            data_pool = self.env['ir.model.data']
            template_pool = self.env['mail.template']
            template_id = data_pool.get_object_reference(
                'hr_salary_certificates', template_xml_ref)[1]
            action_id = self._get_related_window_action_id(data_pool, token)
            if action_id:
                display_link = True
            template_rec = template_pool.browse(template_id)
            if template_rec:
                ctx = {
                    'email_to': email_to,
                    'base_url': base_url,
                    'model': 'emp.salary.certificates',
                    'display_link': display_link,
                    'action_id': action_id,
                }
                if context.get('reason'):
                    ctx.update({'reason': context.get('reason')})

                template_rec.with_context(ctx).send_mail(rec_id, force_send=False)
            return True

    @api.multi
    def generate_service_log(self, state_from=False, state_to=False, reason=''):
        """
        :param state_from:
        :param state_to:
        :return:
        """
        if state_from and state_to:
            self.env['salary.certificates.service.log'].create({
                'salary_certificates_id': self.id,
                'user_id': self.env.user.id,
                'activity_datetime': datetime.today(),
                'state_from': state_from,
                'state_to': state_to,
                'reason': reason,
            })

    @api.multi
    def generate_payslip_amendment(self):
        """
        Generate Payslip
        :return:
        """
        if not self.payslip_amendment_id:
            amendment_wizard_form = self.env.ref(
                'hr_salary_certificates.hsc_generate_payslip_amendment_view',
                False)
            return {
                'name': _('Generate Payslip Amendment'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'res_model': 'hsc.generate.payslip.amendment',
                'views': [(amendment_wizard_form.id, 'form')],
                'view_id': amendment_wizard_form.id,
                'target': 'new',
            }

    @api.multi
    def check_arabic_data(self):
        warning = ''
        if self.bank_id and not self.bank_id.arabic_name:
            warning += 'There is no arabic value for  %s ' % (
                str(self.bank_id.name))
        if self.dest_org_purpose_id and not \
            self.dest_org_purpose_id.arabic_name:
            warning += '\nThere is no arabic value for  %s ' % (
                str(self.dest_org_purpose_id.name))
        if self.destination_organization_type and not \
            self.destination_organization_type.arabic_name:
            warning += '\nThere is no arabic value for ' \
                       'organization type %s ' % (
                str(self.destination_organization_type.name))
        if self.employee_id.country_id and not \
            self.employee_id.country_id.name_eng:
            warning += '\nThere is no arabic value for %s ' % (
                str(self.employee_id.country_id.name))

        if warning:
            raise Warning(_(warning))


    @api.multi
    def check_employee_payslip_data(self):
        """
        Get employee payslip details
        :return:
        """
        for rec in self:
            payslip_rec = self.env['hr.payslip'].search([
                ('employee_id', '=', rec.employee_id.id), ('state',
                                                           '!=', 'cancel'),
                ('display_in_ess', '=', True)],
                order='date_to desc')
            # if not payslip_rec and self.emp_salary_rule_ids:
            #     raise UserError(
            #         _(
            #             'You are not allowed to generate this report until a payslip create.'),
            #     )
    @api.multi
    def get_data(self):
        rule_value_dict = {}
        data = self.get_latest_contract_structure_localdict()
        if data:
            for rule in self.emp_salary_rule_ids:
                if rule.code in data:
                    rule_value_dict.update({
                        rule.code: data[rule.code] or 0.00,
                    })
            total = sum(rule_value_dict.values())
        rule_value_dict.update({'total': total})
        for key, value in rule_value_dict.items():
            rule_value_dict.update({key: '{:0.2f}'.format(abs(value))})
        return rule_value_dict

    @api.multi
    def get_latest_contract_structure_localdict(self):
        blacklist = []
        for rec in self:
            def _sum_salary_rule_category(localdict, category, amount):
                if category.parent_id:
                    localdict = _sum_salary_rule_category(localdict,
                                                          category.parent_id,
                                                          amount)
                localdict[
                    'categories'].dict[category.code] = \
                    category.code in localdict['categories'].dict and \
                    localdict['categories'].dict[category.code] + amount or amount
                return localdict

            class BrowsableObject(object):

                def __init__(self, employee_id, dict, env):
                    self.employee_id = employee_id
                    self.dict = dict
                    self.env = env

                def __getattr__(self, attr):
                    return attr in self.dict and self.dict.__getitem__(attr) or 0.0


            rules_dict = {}
            current_rule_ids = []
            if rec.employee_id.contract_id.struct_id:
                contract_struct_rec = rec.employee_id.contract_id.struct_id \
                    ._get_parent_structure()
                for struct in contract_struct_rec:
                    sort_current_rule_ids = struct.rule_ids.ids
                    current_rule_ids += list(set(sort_current_rule_ids))
            categories = BrowsableObject(rec.employee_id.id, {}, self.env)
            rules = BrowsableObject(rec.employee_id.id, rules_dict, self.env)
            baselocaldict = {'categories': categories, 'rules': rules}
            sorted_rules = rec.emp_salary_rule_ids
            localdict = dict(baselocaldict, employee=rec.employee_id,
                             contract=rec.employee_id.contract_id)
            count = 0
            for rule in sorted_rules:
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                if rule.satisfy_condition(localdict) and rule.id not in \
                    blacklist and rule.id in current_rule_ids:
                    # compute the amount of the rule
                    amount, qty, rate = rule.compute_rule(localdict)
                    count += amount
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the
                    # localdict
                    tot_rule = amount * qty * rate / 100.0
                    # if localdict.get(rule.code):
                    #     tot_rule += localdict.get(rule.code)
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict,
                                                          rule.category_id,
                                                          tot_rule -
                                                          previous_amount)
            return localdict


    @api.model
    def get_current_date(self):
        """
        get current date
        :return:
        """
        return datetime.today().date()


class res_company(models.Model):
    _inherit = "res.company"

    def _get_default_image(self):
        image_path = modules.get_module_resource('hr_salary_certificates',
                                                 'static/src/img',
                                                 'watermark_icon.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))


    watermark_img = fields.Binary(string="Water Mark Image to upload",
                          default=lambda self: self._get_default_image())