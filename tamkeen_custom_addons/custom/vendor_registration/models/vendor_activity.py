from odoo import models, fields, api, _
from lxml import etree
from lxml.builder import E
from collections import defaultdict
from itertools import repeat
from odoo.tools import partition


def name_selection_activity(ids):
    return 'sel_activity_' + '_'.join(map(str, ids))


def name_boolean_activity(id):
    return 'in_activity_' + str(id)


def is_boolean_activity(name):
    return name.startswith('in_activity_')


def is_selection_activity(name):
    return name.startswith('sel_activity_')


def get_boolean_activity(name):
    return int(name[12:])


def get_selection_activity(name):
    return map(int, name[13:].split('_'))


def is_reified_activity(name):
    return is_boolean_activity(name) or is_selection_activity(name)


def parse_m2m(commands):
    "return a list of ids corresponding to a many2many value"
    ids = []
    for command in commands:
        if isinstance(command, (tuple, list)):
            if command[0] in (1, 4):
                ids.append(command[1])
            elif command[0] == 5:
                ids = []
            elif command[0] == 6:
                ids = list(command[2])
        else:
            ids.append(command)
    return ids


class VendorActivitiesCategories(models.Model):
    _name = 'vendor.activities.categories'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    sequence = fields.Integer('Sequence', default=16)
    activities_ids = fields.One2many('vendor.activities', 'category_id',
                                     string='Vendor Activities')
    view_type = fields.Selection([('boolean', 'Boolean'),
                                  ('selection', 'Selection')],
                                 default='boolean', string="View Type")
    note = fields.Text('Note')

    _sql_constraints = [('activities_categories_code_unique', 'UNIQUE(code)',
                         "The code must be unique !")]

    @api.multi
    def write(self, vals):
        """
        :return: 
        """

        if vals and vals.get('view_type'):
            for rec in self:
                for activity_rec in rec.activities_ids:
                    activity_rec.view_type = vals.get('view_type')
        return super(VendorActivitiesCategories, self).write(vals)


class VendorActivities(models.Model):
    _name = 'vendor.activities'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    sequence = fields.Integer('Sequence', default=16)
    category_id = fields.Many2one('vendor.activities.categories',
                                  string='Category')
    view_type = fields.Selection([('boolean', 'Boolean'),
                                  ('selection', 'Selection')],
                                 string="View Type")
    note = fields.Text('Note')
    vendor_reg_ids = fields.Many2many('vendor.registration',
                                      'rel_vendor_regs_activities', 'act_id',
                                      'reg_id', 'Vendors')

    _sql_constraints = [('activities_code_unique', 'UNIQUE(code)',
                         "The code must be unique !")]
    
    @api.onchange('category_id')
    def onchange_category_id(self):
        """
        set view type
        :return: 
        """
        if self.category_id:
            self.view_type = self.category_id.view_type

    @api.model
    def create(self, values):
        user = super(VendorActivities, self).create(values)
        self._update_vendor_activity_view()
        # ir_values.get_actions() depends on action records
        self.env['ir.values'].clear_caches()
        return user

    @api.multi
    def write(self, values):
        res = super(VendorActivities, self).write(values)
        self._update_vendor_activity_view()
        # ir_values.get_actions() depends on action records
        self.env['ir.values'].clear_caches()
        return res

    @api.multi
    def unlink(self):
        res = super(VendorActivities, self).unlink()
        self._update_vendor_activity_view()
        # ir_values.get_actions() depends on action records
        self.env['ir.values'].clear_caches()
        return res

    @api.model
    def _update_vendor_activity_view(self):
        """ Modify the view with xmlid :
        ``vendor_registration.vendor_activity_dummy_form_view``,
        which inherits the Vendor registration form view, and introduces the
        reified activity fields.
        """
        view = self.env.ref(
            'vendor_registration.vendor_activity_dummy_form_view',
            raise_if_not_found=False)
        if view and view.exists() and view._name == 'ir.ui.view':
            # group_no_one = view.env.ref('base.group_no_one')
            xml1, xml2 = [], []
            # xml1.append(E.separator(string=_('Activity'), colspan="2"))
            for app, kind, act in self.get_groups_by_activities():
                attrs = {}
                # code for check group assign group on field
                # if app.xml_id in ('base.module_category_hidden',
                #                   'base.module_category_extra',
                #                   'base.module_category_usability'):
                # attrs['groups'] = 'base.group_no_one'
                if kind == 'selection':
                    # application name with a selection field
                    field_name = name_selection_activity(act.ids)
                    xml1.append(E.field(name=field_name, **attrs))
                    xml1.append(E.newline())
                else:
                    # application separator with boolean fields
                    app_name = app.name or _('Other')
                    xml2.append(E.separator(string=app_name,
                                            colspan="4", **attrs))
                    for act_rec in act:
                        field_name = name_boolean_activity(act_rec.id)
                        xml2.append(E.field(name=field_name, **attrs))
                        # if you want to invisible field based on some
                        # condition then you can do like...
                        # xml2.append(E.field(name=field_name,
                        # invisible="1", **attrs))
                xml2.append({'class': "o_label_nowrap"})
                xml = E.field(E.group(*(xml1), col="2"),
                              E.group(*(xml2), col="4"),
                              name="vendor_activities_ids", position="replace")
                xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY "
                                              "ACTIVITIES"))
                xml_content = etree.tostring(xml, pretty_print=True,
                                             xml_declaration=True,
                                             encoding="utf-8")
                view.with_context(lang=None).write({'arch': xml_content,
                                                    'arch_fs': False})

    @api.model
    def get_groups_by_activities(self):
        """ Return all activities classified by application category,
        as a list::
                [(category, kind, activities), ...],
            where ``category`` and ``activities`` are recordsets,
            and ``kind`` is either ``'boolean'`` or ``'selection'``.
            Category are given in sequence order.  If ``kind`` is
            ``'selection'``, ``activities`` are given in reverse
            implication order.
        """

        def linearize(app, act):
            """
            :param app: activity categories
            :param act: activity
            :return:
            """
            # check app view_type is order is total, i.e., sequence orders are
            # distinct

            if app.view_type == 'boolean':
                return (app, 'boolean', act)
            else:
                return (app, 'selection', act)

        # classify all activity by category
        by_app, others = defaultdict(self.browse), self.browse()
        for g in self.search([]):
            if g.category_id:
                by_app[g.category_id] += g
            else:
                others += g
        # build the result
        res = []
        for app, act in sorted(by_app.iteritems(),
                               key=lambda (a, _): a.sequence or 0):
            res.append(linearize(app, act))
        if others:
            res.append((self.env['vendor.activities.categories'], 'boolean',
                        others))
        return res


class VendorRegistrationView(models.Model):
    _inherit = 'vendor.registration'

    def _remove_reified_activity(self, values):
        """ return `values` without reified group fields """
        add, rem = [], []
        values1 = {}

        for key, val in values.iteritems():
            if is_boolean_activity(key):
                (add if val else rem).append(get_boolean_activity(key))
            elif is_selection_activity(key):
                rem += get_selection_activity(key)
                if val:
                    add.append(val)
            else:
                values1[key] = val
        if 'vendor_activities_ids' not in values and (add or rem):
            # remove group ids in `rem` and add group ids in `add`
            values1['vendor_activities_ids'] = zip(repeat(3), rem) + zip(
                repeat(4), add)
        return values1

    @api.model
    def create(self, values):
        values = self._remove_reified_activity(values)
        return super(VendorRegistrationView, self).create(values)

    @api.multi
    def write(self, vals):
        values = self._remove_reified_activity(vals)
        return super(VendorRegistrationView, self).write(values)

    @api.model
    def default_get(self, fields):
        group_fields, fields = partition(is_reified_activity, fields)
        fields1 = \
            (fields + ['vendor_activities_ids']) if group_fields else fields
        values = super(VendorRegistrationView, self).default_get(fields1)
        self._add_reified_groups(group_fields, values)
        return values

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        # determine whether reified vendor_activities_ids fields are
        # required, and which ones
        fields1 = fields or self.fields_get().keys()
        vendor_activities_field, other_fields = partition(
            is_reified_activity, fields1)
        # read regular fields (other_fields); add 'vendor_activities_ids' if
        #  necessary
        drop_vendor_activities_ids = False
        if vendor_activities_field and fields:
            other_fields.append('vendor_activities_ids')
            drop_vendor_activities_ids = True
        else:
            other_fields = fields
        res = super(VendorRegistrationView, self).read(other_fields, load=load)

        # post-process result to add reified group fields
        if vendor_activities_field:
            for values in res:
                self._add_reified_groups(vendor_activities_field, values)
                if drop_vendor_activities_ids:
                    values.pop('vendor_activities_ids', None)
        return res

    def _add_reified_groups(self, fields, values):
        """ add the given reified group fields into `values` """
        gids = set(parse_m2m(values.get('vendor_activities_ids') or []))
        for f in fields:
            if is_boolean_activity(f):
                values[f] = get_boolean_activity(f) in gids
            elif is_selection_activity(f):
                selected = [gid for gid in get_selection_activity(f) if
                            gid in gids]
                values[f] = selected and selected[-1] or False

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """
        add dynamic fields
        :param allfields:
        :param attributes:
        :return:
        """
        res = super(VendorRegistrationView, self).fields_get(
            allfields, attributes=attributes)
        # add reified groups fields
        for app, kind, act in self.env['vendor.activities'].sudo(

        ).get_groups_by_activities():
            if kind == 'selection':
                # selection group field
                tips = ['%s: %s' % (act_rec.name, act_rec.note) for
                        act_rec in act if act_rec.note]
                res[name_selection_activity(act.ids)] = {
                    'type': 'selection',
                    'string': app.name or _('Other'),
                    'selection': [(False, '')] + [(act_rec.id, act_rec.name)
                                                  for act_rec in act],
                    'help': '\n'.join(tips),
                    'exportable': False,
                    'selectable': False,
                }
            else:
                # boolean group fields
                for act_rec in act:
                    res[name_boolean_activity(act_rec.id)] = {
                        'type': 'boolean',
                        'string': act_rec.name,
                        'help': act_rec.note,
                        'exportable': False,
                        'selectable': False,
                    }
        return res
