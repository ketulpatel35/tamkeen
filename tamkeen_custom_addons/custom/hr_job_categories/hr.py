# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models

import logging

_l = logging.getLogger(__name__)


class hr_job(models.Model):
    _inherit = 'hr.job'

    arabic_name = fields.Char(string='Arabic Name')
    category_ids = fields.Many2many('hr.employee.category',
                                    'job_category_rel', 'job_id',
                                    'category_id', string='Associated Tags')
    active = fields.Boolean(string='Active', default=True)
    # state = fields.Selection([
    #     ('recruit', 'Recruitment in Progress'),
    #     ('open', 'Not Recruiting')
    # ], string='Status', readonly=True, required=True,
    #     track_visibility='always', copy=False, default='open',
    #     help="Set whether the recruitment process is open or closed for this"
    #          " job position.")

    # @api.multi
    # def name_get(self):
    #     res = []
    #     for job in self:
    #         department_name = ''
    #         department_id = job.department_id
    #         if department_id:
    #             department_name = ' ( ' + department_id.name + ' )'
    #         res.append((job.id, job.name + department_name))
    #     return res


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    @api.model
    def _tag_employees(self, employee_id, job_id):
        if not employee_id or not job_id:
            return
        emp_obj = self.env['hr.employee']
        emp_rec = emp_obj.browse(employee_id)
        job_rec = self.env['hr.job'].browse(job_id)
        # _l.warning('tag: emp_rec: %s', emp_rec)
        mail_msg_obj = self.env['mail.message']
        subtype_id = self.env['mail.message.subtype'].search([('name', '=',
                                                               'Discussions')],
                                                             limit=1)
        # mail_msg_obj.create({'subject': emp_rec.name + 'Warning',
        #                      'body': 'tag: emp_rec: %s' % (emp_rec.id),
        #                      'model': 'mail.channel',
        #                      'res_id': 1,
        #                      'message_type': 'notification',
        #                      'record_name': 'general',
        #                      'subtype_id': subtype_id.id or False,
        #                      'channel_ids': [(6, 0,
        #                                       emp_rec.message_channel_ids.ids)
        #                                      ]})
        for categ in job_rec.category_ids:
            # _l.warning('tag: name,id: %s,%s', categ.name, categ.id)
            mail_msg_obj = self.env['mail.message']
            subtype_id = self.env['mail.message.subtype'].search([('name',
                                                                   '=',
                                                                   'Discu'
                                                                   'ssions')],
                                                                 limit=1)
            # mail_msg_obj.create({'subject': categ.name + 'Warning',
            #                      'body': 'tag: name,id: %s,%s' % (
            #                          categ.name, categ.id),
            #                      'model': 'mail.channel',
            #                      'res_id': 1,
            #                      'message_type': 'notification',
            #                      'record_name': 'general',
            #                      'subtype_id': subtype_id.id or False,
            #                      'channel_ids': [(6, 0,
            #                                       categ.message_channel_ids.ids
            #                                       )]})
            if categ.id not in emp_rec.category_ids.ids:
                # _l.warning('tag: write()')
                mail_msg_obj = self.env['mail.message']
                subtype_id = self.env['mail.message.subtype'].search(
                    [('name', '=',
                      'Discussions')],
                    limit=1)
                mail_msg_obj.create({'subject': 'Warning',
                                     'body': 'tag: write()',
                                     'model': 'mail.channel',
                                     'res_id': 1,
                                     'message_type': 'notification',
                                     'record_name': 'general',
                                     'subtype_id': subtype_id.id or False,
                                     })
                emp_rec.write({'category_ids': [(4, categ.id)]})
        return

    @api.model
    def create(self, vals):
        res = super(hr_contract, self).create(vals)
        self._tag_employees(vals.get('employee_id', False),
                            vals.get('job_id', False))
        return res
