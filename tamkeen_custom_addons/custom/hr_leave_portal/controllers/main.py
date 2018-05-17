#-*- coding: utf-8 -*-
import logging

from odoo import _, exceptions, http
from odoo.http import request

_logger = logging.getLogger(__name__)


def get_name_for_lang(lang, model, obj):
    mapping = {
        'ar_SY': {
            'hr.employee': 'name_eng',
            'hr.holidays.status': 'arabic_name',
        },
        'en_US': {
            'hr.employee': 'name',
            'hr.holidays.status': 'name',
        },
    }
    return getattr(obj, mapping[lang][model], False)


class Sync(http.Controller):
    @http.route('/hr/leave/requests', type='json', auth='public', methods=['POST'])
    def get_requests(self, **kw):
        '''
        Get a list of leave requests
        '''
        lang = request.env.context.get('lang', 'en_US')
        _logger.warn(lang)
        keys = [
            'user_id',
            'auth',
        ]
        for k in keys:
            if not kw.get(k, False):
                return {
                    'error': 'Bad Request',
                }
        User = request.env['res.users'].sudo()
        Leave = request.env['hr.holidays'].sudo()
        Employee = request.env['hr.employee'].sudo()

        # Token authentication
        portal_key = request.env['ir.config_parameter'].sudo().get_param('external.portal.uuid', False)
        if portal_key != kw['auth']:
            return {
                'error': 'Bad Request 2',
                'req': kw,
            }
        requests = []
        # get user by email address
        # check if this user is outsource manager
        user = User.search([('login', '=', kw['user_id'])], limit=1)
        if not len(user):
            return {
                'error': 'Bad Request 3',
                'req': kw,
            }
        # here, we must filter employee according to thier outsource manager
        # need access to employee <-> manager lookup table
        employees = Employee.search([])
        requests = []
        for emp in employees:
            temp = dict(
                employee_id=emp.id,
                employee_name=get_name_for_lang(lang, 'hr.employee', emp),
                leaves=[]
            )
            # search leaves by status
            # the default odoo status is "confirm"
            holidays = Leave.search([
                ('employee_id', '=', emp.id),
                ('holiday_type', '=', 'employee'),
                ('state', 'in', ['confirm',]),
                ('type', 'in', ['remove',]),
            ])
            for h in holidays:
                temp['leaves'].append({
                    'id': h.id,
                    'date_from': h.date_from,
                    'date_to': h.date_to,
                    'name': h.name,
                    'notes': h.notes,
                    'number_of_days_temp': h.number_of_days_temp,
                    'number_of_days': h.number_of_days,
                    'date': h.create_date,
                    'status': {
                        'name': get_name_for_lang(lang, 'hr.holidays.status', h.holiday_status_id),
                        'id': h.id,
                    },
                })
            if len(temp['leaves']):
                requests.append(temp)
        return {
            'success': True,
            'requests': requests,
        }

    @http.route('/hr/leave/request/action', type='json', auth='public', methods=['POST'])
    def request_action(self, **kw):
        '''Actions on leave requests (Accept, Decline)
        '''
        keys = [
            'auth',
            'action',
            'id',
        ]
        for k in keys:
            if not kw.get(k, False):
                return {
                    'error': 'Bad Request',
                }
        
        User = request.env['res.users'].sudo()
        Leave = request.env['hr.holidays'].sudo()
        Employee = request.env['hr.employee'].sudo()

        portal_key = request.env['ir.config_parameter'].sudo(
        ).get_param('external.portal.uuid', False)
        if portal_key != kw['auth']:
            return {
                'error': 'Bad Request 2',
                'req': kw,
            }
        # check if the leave request available
        leave = Leave.search([('id', '=', kw['id'])], limit=1)
        if not len(leave):
            return {
                'error': 'Bad Request 3',
                'req': kw,
            }
        # assert the status is "confirm"
        if leave.state != 'confirm':
            return {
                'error': 'Bad Request 4',
                'req': kw,
            }
        state = kw.get('action', 'confirm')
        if state == 'approve':
            state = 'validate'
        if state == 'decline':
            state = 'refuse'
        leave.write({
            'state': state,
            'report_note': kw.get('reasons', leave.report_note)
        })
        return {
            'success': True,
            'request': leave.id,
        }
