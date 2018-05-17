from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import Warning, ValidationError

class ProjectDocuments(models.Model):
    _name = 'project.documents'

    def stage_find(self, section_id, domain=[], order='sequence'):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - section_id: if set, stages must belong to this section or
              be a default stage; if not set, stages must be default
              stages
        """
        # collect all section_ids
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        section_ids.extend(self.mapped('project_id').ids)
        search_domain = []
        if section_ids:
            search_domain = [('|')] * (len(section_ids) - 1)
            for section_id in section_ids:
                search_domain.append(('project_ids', '=', section_id))
        search_domain += list(domain)
        # perform search, return the first found
        return self.env['project.task.type'].search(search_domain,
                                                    order=order, limit=1).id

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False),
                                            ('for_document', '=', True)])

    name = fields.Many2one('documents.category', string='Category')
    project_id = fields.Many2one(
        'project.project', string='Project Name', track_visibility='onchange')
    # document_type = fields.Selection([('url', 'URL'), ('file', 'File')])
    document_type = fields.Selection([('file', 'File')], default='file')
    file_name = fields.Char()
    file_content = fields.Binary(string='File')
    date_upload = fields.Date('Date Uploaded', default=date.today())
    uploaded_by = fields.Many2one('res.users', 'Uploaded By', default=lambda
                                  self: self.env.user.id, track_visibility='onchange')
    url = fields.Char('Url')
    stage_id = fields.Many2one(
        'project.task.type', string='Status', track_visibility='onchange',
        index=True, default=_get_default_stage_id,
        domain="[('project_ids', '=', project_id), ('for_document', '=', True)]",
        copy=False)
    remarks = fields.Text('Remarks')

    @api.multi
    def unlink(self):
        for data in self:
            user_rec = self.env.user
            if not user_rec.has_group('project.group_project_manager'):
                raise ValidationError(
                    _('You are not allowed to delete a record'
                      ' '))
        return super(ProjectDocuments, self).unlink()


class DocumentsCategory(models.Model):
    _name = 'documents.category'

    name = fields.Char('Document Category Name')
