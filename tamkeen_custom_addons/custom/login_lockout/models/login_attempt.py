from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class login_attempt(models.Model):
    _name = "login.attempt"
    _description = 'Login Attempts Counter'
    """
        # id - auto increment
        # address - IP address of client
        # datetime - datetime the user tried the login
    """
    remote_address = fields.Char(string='Remote Address')
    login_datetime = fields.Datetime(string='Login Datetime')
    failed_user_id = fields.Char(string='Failed User')

    @api.model
    def create_login_line(self, remote_address, failed_user_id=''):
        if remote_address:
            now = datetime.datetime.now()
            login_attempt_vals = {
                'login_datetime': now.strftime(DTF),
                'remote_address': remote_address,
                'failed_user_id': failed_user_id,
            }
            new_created_attempt_id = self.create(login_attempt_vals)
            return new_created_attempt_id
        return False

    @api.model
    def check_login_attempts(self, remote_address):
        now = datetime.datetime.now()
        login_attempt_config_pool = self.env['login.attempt.config']
        login_attempt_config_obj = login_attempt_config_pool.browse(self._uid)
        max_attempts_period = -(login_attempt_config_obj.max_attempts_period)
        max_attempts_num = login_attempt_config_obj.max_attempts_num
        now_minus_max_attempts_period = now + datetime.timedelta(
            minutes=max_attempts_period)
        # datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        search_clause = [('remote_address', '=', remote_address),
                         ('login_datetime', '<=',
                          now.strftime(DTF)),
                         ('login_datetime', '>=',
                          now_minus_max_attempts_period.strftime(DTF))
                         ]
        login_attempt_ids = self.search(search_clause, order='id desc',
                                        limit=max_attempts_num)
        if len(login_attempt_ids) < max_attempts_num:
            return False

        return True
