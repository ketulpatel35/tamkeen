# -*- encoding: utf-8 -*-
from odoo import fields, models, api
import datetime


class track_export(models.Model):
    _name = "track.export"
    _description = 'Track Data Export'

    user_name = fields.Char(string='Responsible', readonly=True)
    export_datetime = fields.Datetime(string='Export Datetime', readonly=True)
    exported_object = fields.Char(string='Exported Object', readonly=True)
    exported_fields = fields.Text(string='Exported Object Fields',
                                  readonly=True)
    exported_records_ids = fields.Text(string='Exported Records IDs.',
                                       readonly=True,
                                       help="Empty value means that the user "
                                            "exported all the records.")

    @api.model
    def can_export(self):
        if self.env.user.has_group('web_track_export.group_track_export'):
            return self.env.user.id
        return False

    @api.model
    def create_log_line(self, args):
        if args:
            exported_object = args[0]
            exported_obj_fields = args[1]
            exported_records_ids = args[2]
            now = datetime.datetime.now()
            user_name = self.env.user.name

            export_log_vals = {
                'user_name': user_name,
                'export_datetime': now.strftime("%Y-%m-%d %H:%M:%S"),
                'exported_object': exported_object,
                'exported_fields': exported_obj_fields,
                'exported_records_ids': exported_records_ids,
            }
            self.create(export_log_vals)
            return True
        return False
