from odoo import api, models, fields, _
from odoo.exceptions import Warning
from odoo.http import request
import os
import tempfile
import PythonMagick
import img2pdf
import sys
import PyPDF2


class SalaryCertificatesReportWizard(models.TransientModel):
    _name = 'salary.certificates.report.wizard'

    language = fields.Selection([('english', 'English'), ('arabic',
                                                            'Arabic')],
                                 string='Report Language')

    @api.multi
    def generate_salary_certificates_report(self):
        """
        generate salary certificates report
        :return:
        """
        report_obj = request.env['report']
        context = dict(self._context) or {}
        if context.get('active_ids'):
            for certificate_rec in self.env['emp.salary.certificates'].browse(
                context.get('active_ids')):
                certificate_rec.check_employee_payslip_data()
                if self.language == 'arabic':
                    certificate_rec.check_arabic_data()

                if not certificate_rec._check_group(
                        'hr_salary_certificates.emp_salary_certificates_category_hr_approval'
                ):
                    if certificate_rec.state != 'ready_for_printing':
                        raise Warning(_('Requests should be in ready for '
                                        'printing state to do such action.'))
                # check validation for report printing.
                certificate_rec.check_update_max_report_print()
        report_name = False
        if self.language == 'english':
            report_name = 'hr_salary_certificates.report_salary_english'

        if self.language == 'arabic':
            report_name = 'hr_salary_certificates.report_salary_arabic'
        if report_name:
            report_name = report_name.decode('utf-8')
            pdf = report_obj.get_pdf(context.get('active_ids', []),
                                     report_name, data={})
            # For Get Temp directory
            filepath = tempfile.gettempdir() + '/Salary.pdf'
            f = open(filepath, "w+")
            f.write(pdf)
            f.close()
            pdffilename = filepath
            pdf_im = PyPDF2.PdfFileReader(file(pdffilename, "rb"))
            npage = pdf_im.getNumPages()
            img_lst = []
            for p in range(npage):
                bg_colour = "#ffffff"
                img = PythonMagick.Image()
                img.density('250')
                img.read(pdffilename + '[' + str(p) + ']')
                size = "%sx%s" % (img.columns(), img.rows())
                output_img = PythonMagick.Image(size, bg_colour)
                output_img.type = img.type
                output_img.composite(img, 0, 0,
                                     PythonMagick.CompositeOperator.SrcOverCompositeOp)
                output_img.resize(str(img.rows()))
                output_img.magick('JPG')
                output_img.quality(500)
                output_jpg = tempfile.gettempdir() + '/file_out-' + str(
                    p) + '.png'
                output_img.write(output_jpg)
                img_lst.append(
                    tempfile.gettempdir() + '/file_out-' + str(p) + '.png')
            with open(tempfile.gettempdir() + "/images1.pdf", "wb") as f:
                f.write(img2pdf.convert((img_lst), dpi=500, x=None, y=None))
            attach_id = self.env[
                'salary.certificates.report.download'].create(
                {'name': 'Employment Certificate.pdf',
                 'qweb_output': open(tempfile.gettempdir() + "/images1.pdf",
                                     "rb").read().encode("base64")})
            #
            if img_lst:
                for files in img_lst:
                    os.remove(files)
            os.remove(tempfile.gettempdir() + '/images1.pdf')
            os.remove(tempfile.gettempdir() + '/Salary.pdf')
            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'salary.certificates.report.download',
                'res_id': attach_id.id,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }


class SalaryCertificatesReportDownload(models.TransientModel):
    _name = 'salary.certificates.report.download'

    name = fields.Char('Name')
    qweb_output = fields.Binary(string='Qweb Output')