from datetime import datetime
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from openerp.tools.translate import html_translate
from BeautifulSoup import BeautifulSoup as BSHTML
from odoo.exceptions import ValidationError, UserError

class PdfTemplate(models.Model):
    _name = 'pdf.template.generator'
    _description = 'Pdf Generator'
    _module = 'easy_pdf_creator'

    name = fields.Char('Report Name', required=1, copy=False)
    template_name = fields.Char('Template Name', required=1,
                                translate=html_translate, sanitize_attributes=False, copy=False)
    model_id = fields.Many2one('ir.model', string='Model Name', required=1, copy=False)
    report_format_id = fields.Many2one('report.paperformat', required=1,
                                       string='Report Paper Format', copy=False)
    template = fields.Html(string='Template', required=1, copy=False)
    print_report_name = fields.Char('Printed Report Name', copy=False)
    report_action_id = fields.Many2one('ir.actions.report.xml',
                                       string='Report Action', readonly=True, copy=False)
    html_translate_test = fields.Html('HTML', translate=html_translate,
                                   sanitize_attributes=False, copy=False)
    ir_values_id = fields.Many2one('ir.values', string='More Menu entry', readonly=True,
                                   help='More menu entry.', copy=False,related='report_action_id.ir_values_id')

    @api.constrains('template')
    def check_template(self):
        if BSHTML(self.template).text == '':
            raise ValidationError(_(
                'The Template could not be empty !'))

    @api.multi
    def get_html_field_data(self, field, template_name, id):
        """
        display specific Header in Report
        ---------------------------------
        :param field:
        :return:
        """
        rec = self.search([('template_name', '=', template_name)])
        if rec:
            template_obj = self.env['mail.template']
            if field == 'template':
                if rec.template:
                    if BSHTML(rec.template).text:
                        html_data = template_obj.render_template(
                            rec.template, rec.model_id.model, id)
                        rec.html_translate_test = html_data
                        return rec.id
        return False

    @api.model
    def get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def create_action(self):
        """ Create a contextual action for each report. """

        for report in self:
            report.report_action_id.create_action()
        return True

    @api.multi
    def unlink_action(self):
        """ Remove the contextual actions created for the reports. """
        for report in self:
            report.report_action_id.unlink_action()
        return True
    @api.model
    def get_template_data(self, template_name):
        """
        :param template_name:
        :return:
        """
        temp_data = """<?xml version="1.0"?>
        <t t-name='%s'>
<t t-call="report.html_container">
 <t t-foreach="docs" t-as="o">
  <div class="page">
    <t t-if="o.env['pdf.template.generator'].get_html_field_data('template', '%s', o.id)">
     <t t-raw="o.env['pdf.template.generator'].browse(o.env['pdf.template.generator'].get_html_field_data('template', '%s', o.id)).html_translate_test" itemprop='temp' id='temp'/>
    </t> 
  </div>
 </t>
</t>
</t>"""%(template_name, template_name, template_name)
        return temp_data

    @api.model
    def create(self, vals):
        temp_avai = self.search([('template_name', '=', vals.get(
            'template_name'))])
        if temp_avai:
            raise ValidationError(_(
                'The Template name is already available !'))
        if ' ' in vals.get('template_name'):
            raise ValidationError(_(
                'Space is not allowed in template name'))
        template_full_name = self._module + "." + vals.get('template_name')
        model_name = self.env['ir.model'].browse(vals.get(
            'model_id')).model
        temp_data = self.get_template_data(vals.get('template_name'))
        if model_name and template_full_name:
            # create ir.ui.view record
            ui_view_obj = self.env['ir.ui.view']
            ui_view_vals = {
                'name': vals.get('template_name'),
                'key': template_full_name,
                'active': True,
                'arch': temp_data,
                'type': 'qweb',
                'model': model_name,
                'priority': 16,
                'mode': 'primary',
            }
            view_rec = ui_view_obj.create(ui_view_vals)
            # create model data
            model_data_obj = self.env['ir.model.data']
            ir_model_vals = {
                'complete_name': template_full_name,
                'module': self._module,
                'date_update': self.get_current_datetime(),
                'date_init': self.get_current_datetime(),
                'name': vals.get('template_name'),
                'display_name': template_full_name,
                'model': 'ir.ui.view',
                'res_id': view_rec.id,
                'noupdate': 1,
            }
            model_data_rec = model_data_obj.create(ir_model_vals)
            view_rec.model_data_id = model_data_rec.id
            report_obj = self.env['ir.actions.report.xml']
            report_vals = {
                'name': vals.get('name'),
                'model': model_name,
                'report_type': 'qweb-pdf',
                'report_name': template_full_name,
                'print_report_name': vals.get('print_report_name'),
                'paperformat_id': vals.get('report_format_id', False),
            }
            report_action = report_obj.create(report_vals)
            report_action.create_action()
            vals['report_action_id'] = report_action.id

        return super(PdfTemplate, self).create(vals)

    @api.multi
    def unlink(self):
        for rec in self:
            ir_ui_view = self.env['ir.ui.view'].search([('name', '=',
                                                         rec.template_name)])
            if ir_ui_view:
                if ir_ui_view.model_data_id:
                    ir_ui_view.model_data_id.unlink()
                ir_ui_view.unlink()
            report_action = self.env['ir.actions.report.xml'].search([(
                'name', '=', rec.name)])
            if report_action:
                report_action.unlink()

        return super(PdfTemplate, self).unlink()