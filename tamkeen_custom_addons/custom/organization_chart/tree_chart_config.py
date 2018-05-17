# -*- coding: utf-8 -*-
##############################################################################

from collections import OrderedDict
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning

THEME = [('annabel', 'Annabel'), ('sara', 'Sara'), ('belinda', 'Belinda'),
         ('cassandra', 'Cassandra'), ('deborah', 'Deborah'), ('lena', 'Lena'),
         ('monica', 'Monica'), ('ula', 'Ula'), ('eve', 'Eve'),
         ('tal', 'Tal'), ('vivian', 'Vivian'), ('ada', 'Ada'), ('helen', 'Helen'),
]

COLOR = [('darkred', 'Darkred'), ('pink', 'Pink'), ('darkorange', 'Darkorange'),   
         ('orange', 'Orange'), ('lightgreen', 'Lightgreen'), ('green', 'Green'),   
         ('lightteal', 'Lightteal'), ('teal', 'Teal'), ('blue', 'Blue'),
         ('darkpurple', 'Darkpurple'), ('purple', 'Purple'), ('mediumdarkblue', 'Mediumdarkblue'),
         ('darkblue', 'Darkblue'), ('cordovan', 'Cordovan'), ('darkcordovan', 'Darkcordovan'),
         ('neutralgrey', 'Neutralgrey'), ('black', 'Black')        
]

LINK = [('m', 'M'), ('b', 'B')]
ORIENTATION = [ ('RO_TOP', 'RO_TOP'), ('RO_BOTTOM', 'RO_BOTTOM'), ('RO_RIGHT', 'RO_RIGHT'),   
                ('RO_LEFT', 'RO_LEFT'), ('RO_TOP_PARENT_LEFT', 'RO_TOP_PARENT_LEFT'), ('RO_BOTTOM_PARENT_LEFT', 'RO_BOTTOM_PARENT_LEFT'),
                ('RO_RIGHT_PARENT_TOP', 'RO_RIGHT_PARENT_TOP'), ('RO_LEFT_PARENT_TOP', 'RO_LEFT_PARENT_TOP'),     
]

class tree_chart_config(models.Model):
    _name = "tree.chart.config"
    _description = "Tree Chart Configuration"
    _inherit = ['mail.thread']

    @api.model
    def _get_default_model(self):
        res = self.env['ir.model'].search([('model','=',
                                                  'hr.department')])
        return res and res[0] or False

    name = fields.Char(string='Name', required=True, translate=True)
    ##Theme Info##
    theme_type = fields.Selection(THEME, string='Theme Type', required=True)
    color = fields.Selection(COLOR, string='Color', required=True)
    linkType =fields.Selection(LINK, 'Link Type', required=True)
    orientation = fields.Selection(ORIENTATION, 'Orientation', required=True)
    expandToLevel = fields.Integer('Expand To Level', default=2)
    enableEdit = fields.Boolean('Enable Edit')
    enableZoom = fields.Boolean('Enable Zoom')
    enableSearch = fields.Boolean('Enable Search')
    enableGridView = fields.Boolean('Enable Grid View')
    enableDetailsView = fields.Boolean('Enable Details View')
    enablePrint= fields.Boolean('Enable Print')
    ##############
    model_id = fields.Many2one('ir.model', 'Model', required=True, default=_get_default_model)
    line_ids = fields.One2many('tree.chart.line', 'tree_id', 'Tree Lines',
                               required=True)
    related_url = fields.Text('Related Chart URL', help="The link that will "
                                                       "be used to access this chart as web page.")
    related_menu_id = fields.Many2one('ir.ui.menu', 'Related Menu Item',
                                     help="The menu that will be used to access this chart as web page.")
    active = fields.Boolean('Active', default=True)

    @api.model
    def create(self, vals):
        marked_parent_fields = marked_photo_fields = []
        tree_line_pool = self.env['tree.chart.line']
        if vals.get('line_ids', False):
            chart_line_ids = vals.get('line_ids')
            for line in chart_line_ids:
                if line[2]['field_usage'] == 'parent':
                    marked_parent_fields.append(line[2]['field_usage'])
                if line[2]['field_usage'] == 'photo':
                    marked_photo_fields.append(line[2]['field_usage'])
            if len(marked_parent_fields) > 1:
                raise Warning(_("You should have only one field marked as "
                              "Parent Field."))
            if len(marked_photo_fields) > 1:
                raise Warning(_("You should have only one field marked as "
                               "Photo Field."))
        return super(tree_chart_config, self).create(vals)

    @api.multi
    def write(self, vals):
        tree_line_pool = self.env['tree.chart.line']
        marked_parent_fields = tree_line_pool.search([('tree_id','=',
                                                       self._ids[0]),
                                                      ('field_usage','=','parent')])
        if len(marked_parent_fields) > 1:
            raise Warning(_("You should have only one field marked as Parent "
                      "Field."))
        marked_photo_fields = tree_line_pool.search([('tree_id','=', self._ids[0]),('field_usage','=','photo')])
        if len(marked_photo_fields) > 1:
            raise Warning(_("You should have only one field marked as Photo "
                            "Field."))
        return super(tree_chart_config, self).write(vals)

    @api.multi
    def generate_link(self):
        for rec in self:
            if rec.name:
                related_url = '/tree_chart/' + str(
                    rec.name.lower().replace(" ", "_")) + '/' + str(
                    rec.id)
            rec.write({'related_url': related_url})
        return related_url

    @api.multi
    def generate_menu_item(self):
        act_url_data = menu_data = {}
        for rec in self:
            related_url = rec.generate_link()
            if related_url:
                act_url_obj = self.env['ir.actions.act_url']
                tree_url_tag = '/' + str(self._ids[0])
                act_url_rec = act_url_obj.sudo().search([('url', 'like',
                                                        tree_url_tag)])
                if act_url_rec:
                    act_url_data = {
                        'name': rec.name,
                        'url': related_url,
                    }
                    act_url_rec.sudo().write(act_url_data)
                else:
                    act_url_data = {
                        'target': 'new',
                        'name': rec.name,
                        'type': 'ir.actions.act_url',
                        'url': related_url,
                    }
                    act_url_rec = act_url_obj.sudo().create(act_url_data)
                menu_item_id = rec.related_menu_id
                if not menu_item_id:
                    menu_pool = self.env['ir.ui.menu']
                    data_pool = self.env['ir.model.data']
                    default_parent_menu_id = \
                    data_pool.get_object_reference('organization_chart',
                                                   'configuration_menu')[1]
                    if default_parent_menu_id:
                        menu_data = {
                            'name': rec.name,
                            'parent_id': default_parent_menu_id,
                            'action': 'ir.actions.act_url,%s' % (act_url_rec.id,),
                            'sequence': 100,
                        }
                        related_menu_rec = menu_pool.sudo().create(
                            menu_data)
                        self.sudo().write(
                                   {'related_menu_id': related_menu_rec.id})
        return True

    @api.onchange('model_id')
    def onchange_model_id(self):
        self.line_ids = False

    def _concatenate_fields(self, rel_object, fields_list):
        #concatenate 3 levels
        #field list should be in sequence.
        mapped_object = False
        if fields_list:
            mapped_object = getattr(rel_object, fields_list[0])
            if len(fields_list) == 2:
                mapped_object = getattr(mapped_object,fields_list[1]) or False
        return mapped_object

    def _get_fields_list_data(self, rec, rec_info, fields_list):
        fields_list_data = []
        if fields_list:
            print fields_list
            for key in fields_list:
                if fields_list[key][1] not in ['many2one','one2many',
                                               'many2many']:
                    rec_info[key] = self._concatenate_fields(rec, [key])
                elif fields_list[key][1] == 'many2one':
                    rel_id_exist = self._concatenate_fields(rec,[key])
                    if rel_id_exist:
                        rel_name = self._concatenate_fields(rel_id_exist,['name'])
                        rec_info[key] = rel_name
                elif fields_list[key][1] in ['one2many','many2many']:
                    rec_info[key] = len(self._concatenate_fields(rec, [key]))
                fields_list_data.append(key)
        return fields_list_data
        
    def _get_rec_related_information(self, tree_chart, rec):
        rec_info = {}
        primary_fields = {}
        secondary_fields = {}
        parent_id = parentIdField = False
        photoField = '/organization_chart/static/src/img/emp.png'
        for line in tree_chart.line_ids:
            if line.field_usage == 'parent':
                parentIdField = str(line.field_id.name)
                parent_id = int(self._concatenate_fields(rec, [parentIdField,'id']))
            elif line.field_usage == 'photo':
                photoField = str(line.field_id.name)
                photoField = self._concatenate_fields(rec, [photoField])
            elif line.field_usage == 'primary':
                primary_fields.update({
                   line.field_id.name: [line.field_id.name,line.field_id.ttype],
                })
            elif line.field_usage == 'secondary':
                secondary_fields.update({
                   line.field_id.name: [line.field_id.name,line.field_id.ttype],
                })
        primaryFields = self._get_fields_list_data(rec, rec_info, primary_fields) or False
        secondaryFields = self._get_fields_list_data(rec, rec_info, secondary_fields) or False
        
        rec_info.update({
            'id': rec.id,
            'parentId': parent_id,
            'parentIdField': parentIdField,
            'primaryFields': primaryFields,
            'secondaryFields': secondaryFields,
            'photoField': photoField,
            
        })
        return rec_info

    @api.model
    def draw_tree_structure(self, args):
        if self._context is None:
            context = {}
        rec_tree_data = rec_info = []
        result = rec_line_info = {}
        tree_id = int(args[0]) or 0
        tree_chart_rec = self.search([('id','=',tree_id)], limit=1)
        #self.search(cr, uid, [('write_uid','=',uid)], limit=1, order="write_date desc",context=context)
        if tree_chart_rec:
            for tree_chart in tree_chart_rec:
                # model_pool = self.pool[tree_chart.model_id.model]
                model_pool = self.env[str(tree_chart.model_id.model)]
                model_record_rec = model_pool.search([])
                if model_record_rec:
                    for rec in model_record_rec:
                        rec_info = self._get_rec_related_information(tree_chart, rec)
                        if rec_info:
                            rec_line_info = OrderedDict()
                            rec_line_info['id'] = rec_info['id']
                            rec_line_info['parentId'] = rec_info['parentId']
                            for rec in rec_info:
                                if rec not in ['primaryFields','secondaryFields', 'photoField']:
                                    rec_line_info[rec] = rec_info[rec] 
                            rec_line_info['rec_manager_pic'] = rec_info['photoField']
                            # rec_line_info['rec_manager_pic'] = rec_info['rec_manager_pic']        
                            rec_tree_data.append(rec_line_info)
                    result.update({
                        'theme_type': tree_chart.theme_type,
                        'color': tree_chart.color,
                        'enableEdit': tree_chart.enableEdit,
                        'enableZoom': tree_chart.enableZoom,
                        'enableSearch': tree_chart.enableSearch,
                        'enableGridView': tree_chart.enableGridView,
                        'expandToLevel': tree_chart.expandToLevel,
                        'linkType': tree_chart.linkType,
                        'orientation': tree_chart.orientation,
                        'enableDetailsView': tree_chart.enableDetailsView,
                        'enablePrint': tree_chart.enablePrint,
                        ####
                        'parentIdField': rec_info['parentIdField'],
                        'primaryFields': rec_info['primaryFields'],
                        'photoFields': rec_info['photoField'],
                        'rec_tree_data': rec_tree_data,
                    }) 
        
        return result


class tree_chart_line(models.Model):
    _name = 'tree.chart.line'
    _description = 'Tree Chart Line'
    _order = "sequence"

    @api.model
    def _get_model_id(self):
        if self._context.get('model_id', False):
            return self._context.get('model_id', False)
        return False

    sequence = fields.Integer(string='Sequence', help="Gives the sequence of this "
                                              "line when displaying the data.")
    model_id = fields.Many2one('ir.model', 'Model', invisible=True,
                             required=True, default=_get_model_id)
    tree_id = fields.Many2one('tree.chart.config', 'Tree Chart',
                             ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', 'Field Name', required=True,
                             domain="[('model_id', '=', model_id)]")
    field_usage = fields.Selection([('primary', 'Primary Field'),
                                    ('secondary', 'Secondary Field'),
                                    ('parent', 'Parent Field'),('photo',
                                                                'Photo '
                                                                'Field')],
                                   'Field Usage', required=True, default='primary')
