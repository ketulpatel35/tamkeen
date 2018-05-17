# -*- encoding: utf-8 -*-
from odoo import models, api


class track_delete(models.Model):
    _name = "track.delete"
    _description = 'Track Data Deletion'

    @api.model
    def can_delete(self):
        """
        :return:
        """
        if self.env.user.has_group('web_track_delete.group_track_delete'):
            return self.env.user.id
        return False
