from odoo import fields, fields, api, models
from odoo.addons.hr_infraction.models.hr_infraction import \
    ACTION_TYPE_SELECTION


class action_wizard(models.TransientModel):
    _name = 'hr.infraction.action.wizard'
    _description = 'Choice of Actions for Infraction'

    action_type = fields.Selection(ACTION_TYPE_SELECTION, string='Action')
    memo = fields.Text(string='Notes')
    new_job_id = fields.Many2one('hr.job', string='New Job')
    xfer_effective_date = fields.Date(string='Effective Date')
    effective_date = fields.Date(string='Effective Date')

    @api.multi
    def create_action(self):
        if not self._context:
            context = {}
        else:
            context = dict(self._context)

        infraction_id = context.get('active_id', False)
        if not infraction_id:
            return False
        data = self.read()
        vals = {
            'infraction_id': infraction_id,
            'type': data[0]['action_type'],
            'memo': data[0].get('memo', False),
        }
        action_id = self.env['hr.infraction.action'].create(vals)

        # Update state of infraction, if not already done so

        infraction_obj = self.env['hr.infraction']
        infraction_rec = infraction_obj.browse(infraction_id)
        infraction_data = infraction_rec.read(['employee_id', 'state'])[0]
        if infraction_data['state'] == 'confirm':
            infr_rec = self.env['hr.infraction'].browse(infraction_id)
            infr_rec.state = 'action'

        imd_obj = self.env['ir.model.data']
        iaa_obj = self.env['ir.actions.act_window']

        # If the action is a warning create the appropriate record,
        # reference it from the action,
        # and pull it up in the view (in case the user needs to make any
        # changes.

        if data[0]['action_type'] in ['warning_verbal', 'warning_letter']:
            vals = {
                'name':
                    (data[0]['action_type'] ==
                     'warning_verbal' and 'Verbal'or 'Written') +
                    ' Warning',
                'type':
                    data[0]['action_type'] ==
                    'warning_verbal' and 'verbal' or 'written',
                'action_id': action_id.id,
            }
            warning_id = self.env['hr.infraction.warning'].create(vals)
            action_id.warning_id = warning_id.id

            res_model, res_id = imd_obj.get_object_reference(
                'hr_infraction', 'open_hr_infraction_warning')
            iaa_rec = iaa_obj.browse(res_id)
            # dict_act_window = res_id.read(res_id)
            dict_act_window = iaa_rec.read()[0]
            dict_act_window['view_mode'] = 'form,tree'
            dict_act_window['domain'] = [('id', '=', warning_id.id)]
            return dict_act_window

        # If the action is a departmental transfer create the appropriate
        #     record, reference it from
        # the action, and pull it up in the view (in case the user needs to
        #     make any changes.
        elif data[0]['action_type'] == 'transfer':
            xfer_obj = self.env['hr.department.transfer']
            vals = {
                'employee_id': infraction_rec.employee_id.id,
                'dst_id': data[0]['new_job_id'][0],
                'date': data[0]['xfer_effective_date'],
            }
            xfer_new_rec = xfer_obj.create(vals)
            xfer_new_rec.onchange_employee()
            action_id.transfer_id = xfer_new_rec.id
            res_model, res_id = \
                imd_obj.get_object_reference(
                    'hr_transfer', 'open_hr_department_transfer')
            iaa_rec = iaa_obj.browse(res_id)
            dict_act_window = iaa_rec.read()[0]
            dict_act_window['view_mode'] = 'form,tree'
            dict_act_window['domain'] = [('id', '=', xfer_new_rec.id)]
            return dict_act_window

        # The action is dismissal. Begin the termination process.
        #
        elif data[0]['action_type'] == 'dismissal':
            term_obj = self.env['hr.employee.termination']
            # wkf = netsvc.LocalService('workflow')
            ee = self.env['hr.employee'].browse(
                infraction_data['employee_id'][0])

            # We must create the employment termination object before we set
            # the contract state to 'done'.
            res_model, res_id = imd_obj.get_object_reference(
                'hr_infraction', 'term_dismissal')
            vals = {
                'employee_id': ee.id,
                'name': data[0]['effective_date'],
                'reason_id': res_id,
            }
            term_id = term_obj.create(vals)
            action_id.termination_id = term_id.id

            # End any open contracts
            for contract in ee.contract_ids:
                if contract.state not in ['done']:
                    contract.state = 'pending'
                    # wkf.trg_validate(
                    #     uid, 'hr.contract', contract.id,
                    # 'signal_pending_done', cr)

            # Set employee state to pending deactivation
            # wkf.trg_validate(
            #     uid, 'hr.employee', ee.id, 'signal_pending_inactive', cr)

            # Trigger confirmation of termination record
            term_id.state = 'confirm'
            # wkf.trg_validate(
            #     uid, 'hr.employee.termination', term_id,
            # 'signal_confirmed', cr)

            res_model, res_id = imd_obj.get_object_reference(
                'hr_employee_state', 'open_hr_employee_termination')
            iaa_rec = iaa_obj.browse(res_id)
            dict_act_window = iaa_rec.read()[0]
            dict_act_window['domain'] = [('id', '=', term_id.id)]
            return dict_act_window

        return True
