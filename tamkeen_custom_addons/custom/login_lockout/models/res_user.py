from odoo import api, fields, models, SUPERUSER_ID
import datetime
import logging

_logger = logging.getLogger(__name__)


class res_users(models.Model):
    _inherit = 'res.users'

    deactivate_reason = fields.Selection([('hacked', 'Hacked'),
                                          ('locked', 'Locked')],
                                         string='Last Deactivation Reason')
    deactivate_time = fields.Datetime(string='Last Deactivation Time',
                                      readonly=True)
    activate_time = fields.Datetime(string='Last Activation Time',
                                    readonly=True)

    # this function is not check functionaly because it will from single_login\
    #     module and its not migrated
    #     return user_id
    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        # def authenticate(self, db, login, password, user_agent_env):
        """Verifies and returns the user ID corresponding to the given
          ``login`` and ``password`` combination, or False if there was
          no matching user.

           :param str db: the database on which user is trying to authenticate
           :param str login: username
           :param str password: user password
           :param dict user_agent_env: environment dictionary describing any
               relevant environment attributes
        """
        uid = super(res_users, cls).authenticate(db=db, login=login,
                                                 password=password,
                                                 user_agent_env=user_agent_env)

        if not uid:
            if user_agent_env and user_agent_env.get('base_location'):
                # cr = self.env.get_db(db).cursor()
                try:
                    with cls.pool.cursor() as cr:
                        remote_address = user_agent_env['REMOTE_ADDR']
                        self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                        login_attempt_pool = self.env['login.attempt']
                        failed_user_id = self.search([('login', '=', login)],
                                                     limit=1)
                        if failed_user_id:
                            user_info = str(login) + ' with ID: ' + str(
                                failed_user_id)
                        else:
                            user_info = str(login)
                        login_attempt_pool.create_login_line(
                            remote_address,
                            user_info)
                        cr.commit()
                        # for counting the number of failed attempts
                        exceeded_limit = \
                            login_attempt_pool.check_login_attempts(
                                remote_address)
                        if exceeded_limit:
                            if failed_user_id:
                                self.lock_user(failed_user_id)
                except Exception:
                    _logger.exception("Failed to create a new failed login "
                                      "attempt.")
                    # mail_msg_obj = self.env['mail.message']
                    # subtype_id = self.env['mail.message.subtype'].search([
                    #     ('name', '=', 'Discussions')], limit=1)
                    # mail_msg_obj.create({'subject': 'Exception',
                    #                      'body': "Failed to create a new "
                    #                              "failed login "
                    #                              "attempt.",
                    #                      'model': 'mail.channel',
                    #                      'res_id': 1,
                    #                      'message_type': 'notification',
                    #                      'record_name':
                    #  'general',
                    #                      'subtype_id':
                    #  subtype_id.id or False,
                    #                      })
                    # finally:
                    #     cr.close()
        return uid

    @api.model
    def lock_user(self, failed_user_id):
        try:
            self._cr.execute("UPDATE res_users SET active=False, "
                             "deactivate_time=now() AT TIME ZONE 'UTC', "
                             "deactivate_reason='hacked' WHERE id=%s",
                             (failed_user_id.id,))

            self._cr.commit()
        except Exception:
            _logger.debug("Failed to deactivate the user with login",
                          exc_info=True)
            # mail_msg_obj = self.env['mail.message']
            # subtype_id = self.env['mail.message.subtype'].search([
            #     ('name', '=', 'Discussions')], limit=1)
            # mail_msg_obj.create({'subject': 'Debug',
            #                      'body': "Failed to
            #  deactivate the user with "
            #                              "login",
            #                      'model': 'mail.channel',
            #                      'res_id': 1,
            #                      'message_type': 'notification',
            #                      'record_name': 'general',
            #                      'subtype_id': subtype_id.id or False,
            #                      })
        return True

    @api.model
    def cron_unlock_users(self):
        login_attempt_config_pool = self.env['login.attempt.config']
        login_attempt_config_obj = login_attempt_config_pool.search([])
        if len(login_attempt_config_obj) <= 0:
            _logger.warning('You have to create login attept config recoed')
            # mail_msg_obj = self.env['mail.message']
            # subtype_id = self.env['mail.message.subtype'].search([
            #     ('name', '=', 'Discussions')], limit=1)
            # mail_msg_obj.create({'subject': 'Warning',
            #                      'body': 'You have to create login attept '
            #                              'config recoed',
            #                      'model': 'mail.channel',
            #                      'res_id': 1,
            #                      'message_type': 'notification',
            #                      'record_name': 'general',
            #                      'subtype_id': subtype_id.id or False,
            #                      })
            vals = {
                'max_attempts_period': 5,
                'max_unlock_period': 5,
                'max_attempts_num': 5,
            }
            self.env['login.attempt.config'].create(vals)
        else:
            login_attempt_config_obj = login_attempt_config_obj[0]
        max_attempts_period = \
            -(int(login_attempt_config_obj.max_attempts_period))

        now = datetime.datetime.now()
        now_minus_max_attempts_period = now + datetime.timedelta(
            minutes=max_attempts_period)
        # datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        search_clause = [('deactivate_reason', '=', 'hacked'),
                         ('active', '=', False),
                         ('deactivate_time', '<=',
                          now_minus_max_attempts_period.strftime(
                              "%Y-%m-%d %H:%M:%S")),
                         ]
        locked_users_ids = self.search(search_clause)
        for user_id in locked_users_ids:
            try:
                self._cr.execute("UPDATE res_users SET active=True,"
                                 "activate_time=now() AT TIME ZONE 'UTC' "
                                 "WHERE id=%s", (user_id.id,))
                self._cr.commit()
            except Exception:
                _logger.debug("Failed to deactivate the user with login",
                              exc_info=True)
                # mail_msg_obj = self.env['mail.message']
                # subtype_id = self.env['mail.message.subtype'].search([
                #     ('name', '=', 'Discussions')], limit=1)
                # mail_msg_obj.create({'subject': 'Debug',
                #                      'body': "Failed to deactivate the user "
                #                              "with login",
                #                      'model': 'mail.channel',
                #                      'res_id': 1,
                #                      'message_type': 'notification',
                #                      'record_name': 'general',
                #                      'subtype_id': subtype_id.id or False,
                #                      })
        return True
