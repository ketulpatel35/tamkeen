from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import datetime


class ProjectCode(models.TransientModel):
    _name = 'project.project.code'

    @api.depends('current_code','override_code','prefix','project_type')
    def _get_project_year(self):
        if self._context and self._context.get('actual_start_date'):
            if datetime.datetime.strptime(self._context.get('actual_start_date'),
                                           DEFAULT_SERVER_DATE_FORMAT):
                self.project_year = datetime.datetime.strptime(self._context.get('actual_start_date'),
                                           DEFAULT_SERVER_DATE_FORMAT).year
        if not self._context.get('actual_start_date'):
            self.project_year = datetime.datetime.now().date().year


    current_code = fields.Char(string='Current Code')
    override_code = fields.Boolean('Override Code')
    prefix = fields.Char(string='Prefix', default='PJ' ,readonly=False)
    project_type = fields.Selection([('internal', 'Internal'),
                                     ('external', 'External')],
                                    string='Project Type')

    project_year = fields.Char(string='Project Year',
                               compute=_get_project_year)
    suffix = fields.Char(string='Suffix')


    @api.multi
    def generate_code(self):
        for rec in self:
            active_project = self.env['project.project'].browse(self._context.get('active_id'))
            prefix = rec.prefix
            type_txt = ''
            year = rec.project_year
            suffix =rec.suffix
            final_string = ''
            if rec.project_type == 'internal':
                type_txt = 'INT'
            if rec.project_type == 'external':
                type_txt ='EXT'
            if prefix:
                final_string += prefix
            if type_txt:
                final_string += '/'+type_txt
            if year:
                final_string += '/'+year
            if active_project.code:
                final_string += '/'+active_project.code
            if suffix:
                final_string += '/'+suffix
        active_project.project_code = final_string