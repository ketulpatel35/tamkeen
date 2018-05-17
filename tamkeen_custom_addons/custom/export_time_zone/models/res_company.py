from odoo import models, fields, api
import pytz


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def tz_get(self):
        # put POSIX 'Etc/*' entries at the end to avoid confusing
        # users - see bug 1086728
        return [(tz, tz) for tz in sorted(pytz.all_timezones,
                                          key=lambda tz: tz if not
                                          tz.startswith('Etc/') else '_')]
