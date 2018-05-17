from odoo.models import BaseModel
from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import pytz


def __export_xml_id(self):
    """ Return a valid xml_id for the record ``self``. """
    if not self._is_an_ordinary_table():
        raise Exception(
            "You can not export the column ID of model %s, because the "
            "table %s is not an ordinary table."
            % (self._name, self._table))
    ir_model_data = self.sudo().env['ir.model.data']
    data = ir_model_data.search([('model', '=', self._name), ('res_id', '=', self.id)])
    if data:
        if data[0].module:
            return '%s.%s' % (data[0].module, data[0].name)
        else:
            return data[0].name
    else:
        postfix = 0
        name = '%s_%s' % (self._table, self.id)
        while ir_model_data.search([('module', '=', '__export__'), ('name', '=', name)]):
            postfix += 1
            name = '%s_%s_%s' % (self._table, self.id, postfix)
        ir_model_data.create({
            'model': self._name,
            'res_id': self.id,
            'module': '__export__',
            'name': name,
        })
        return '__export__.' + name


@api.multi
def _export_rows1(self, fields):
    """ Export fields of the records in ``self``.

        :param fields: list of lists of fields to traverse
        :return: list of lists of corresponding values
    """
    lines = []
    for record in self:
        # main line of record, initially empty
        current = [''] * len(fields)
        lines.append(current)

        # list of primary fields followed by secondary field(s)
        primary_done = []

        # process column by column
        for i, path in enumerate(fields):
            if not path:
                continue

            name = path[0]
            if name in primary_done:
                continue

            if name == '.id':
                current[i] = str(record.id)
            elif name == 'id':
                current[i] = record.__export_xml_id()
            else:
                field = record._fields[name]
                value = record[name]
                if field.type == 'datetime' and value:
                    value = datetime.strptime(value, DEFAULT_SERVER_DATETIME_FORMAT)
                    tz_name = record._context.get('selected_tz', 'UTC')
                    if not tz_name:
                        tz_name = 'UTC'
                    utc_timestamp = pytz.utc.localize(value, is_dst=False)
                    context_tz = pytz.timezone(tz_name)
                    value = utc_timestamp.astimezone(context_tz)
                    value = value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                # this part could be simpler, but it has to be done this way
                # in order to reproduce the former behavior
                if not isinstance(value, BaseModel):
                    current[i] = field.convert_to_export(value, record)
                else:
                    primary_done.append(name)

                    # This is a special case, its strange behavior is intended!
                    if field.type == 'many2many' and len(path) > 1 and path[1] == 'id':
                        xml_ids = [r.__export_xml_id() for r in value]
                        current[i] = ','.join(xml_ids) or False
                        continue

                    # recursively export the fields that follow name
                    fields2 = [(p[1:] if p and p[0] == name else []) for p in fields]
                    lines2 = value._export_rows(fields2)
                    if lines2:
                        # merge first line with record's main line
                        for j, val in enumerate(lines2[0]):
                            if val or isinstance(val, bool):
                                current[j] = val
                        # check value of current field
                        if not current[i] and not isinstance(current[i], bool):
                            # assign xml_ids, and forget about remaining lines
                            xml_ids = [item[1] for item in value.name_get()]
                            current[i] = ','.join(xml_ids)
                        else:
                            # append the other lines at the end
                            lines += lines2[1:]
                    else:
                        current[i] = False

    return lines


BaseModel._export_rows = _export_rows1
BaseModel.__export_xml_id = __export_xml_id
