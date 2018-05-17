from odoo import api, fields, models


class login_attempt_config_wizard(models.TransientModel):
    _name = 'login.attempt.config.wizard'
    _inherit = 'res.config.settings'

    module_max_attempts_period = fields.Integer(string='Max Attempts Period',
                                                default=lambda *a: 5,
                                                help="The period that the "
                                                     "system will allow for "
                                                     "logging.")
    module_max_unlock_period = fields.Integer(string='Max Period To Unlock',
                                              default=lambda *a: 5,
                                              help="The period that the "
                                                   "system will unlock the "
                                                   "user after it.")
    module_max_attempts_num = fields.Integer(string='Max Attempts Number',
                                             default=lambda *a: 5,
                                             help="The maximum number of "
                                                  "attempts the hacker can "
                                                  "attempt in the given "
                                                  "period.")

    @api.model
    def default_get(self, fields):
        login_attempt_config_pool = self.env['login.attempt.config']
        res = super(login_attempt_config_wizard, self).default_get(fields)
        login_attempt_config_rec = login_attempt_config_pool.search([],
                                                                    limit=1)
        if login_attempt_config_rec:
            vals = {
                'module_max_attempts_period':
                    login_attempt_config_rec.max_attempts_period,
                'module_max_attempts_num':
                    login_attempt_config_rec.max_attempts_num,
                'module_max_unlock_period':
                    login_attempt_config_rec.max_unlock_period,
            }
            res.update(vals)
        return res

    @api.multi
    def save_record(self):
        login_attempt_config_pool = self.env['login.attempt.config']
        for data in self:
            vals = {
                'max_attempts_period': data.module_max_attempts_period,
                'max_unlock_period': data.module_max_unlock_period,
                'max_attempts_num': data.module_max_attempts_num,
            }
        login_attempt_config_rec = login_attempt_config_pool.search([])
        if login_attempt_config_rec:
            login_attempt_config_rec.write(vals)
        else:
            login_attempt_config_rec = login_attempt_config_pool.create(vals)
        return login_attempt_config_rec


class login_attempt_config(models.Model):
    _name = "login.attempt.config"
    _description = 'Login Attempts Configuration'

    max_attempts_period = fields.Integer(string='Max Attempts Period',
                                         default=lambda *a: 5,
                                         help="The period that the system "
                                              "will allow for logging.")
    max_unlock_period = fields.Integer(string='Max Period To Unlock',
                                       default=lambda *a: 5,
                                       help="The period that the system will "
                                            "unlock the user after it.")
    max_attempts_num = fields.Integer(string='Max Attempts Number',
                                      default=lambda *a: 5,
                                      help="The maximum number of attempts "
                                           "the hacker can attempt in the "
                                           "given period.")
