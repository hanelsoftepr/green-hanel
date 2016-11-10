# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp.addons.web.controllers.main import ExportFormat, content_disposition
from openerp.http import request
import operator
import simplejson


# Define new function based on odoo function
def base(self, data, token):
    params = simplejson.loads(data)
    model, fields, ids, domain, import_compat = \
        operator.itemgetter('model', 'fields', 'ids', 'domain',
                            'import_compat')(
            params)

    Model = request.session.model(model)
    context = dict(request.context or {}, **params.get('context', {}))
    if params.get('import_compat', False) == 'flexible':
        context.update({'flexible_data': True})
        import_compat = False
    context.update({'depth': [0]})

    ids = ids or Model.search(domain, 0, False, False, context)
    if not request.env[model]._is_an_ordinary_table():
        fields = [field for field in fields if field['name'] != 'id']

    field_names = map(operator.itemgetter('name'), fields)
    import_data = Model.export_data(ids, field_names, self.raw_data, context=context).get('datas', [])

    if import_compat:
        columns_headers = field_names
    else:
        columns_headers = [val['label'].strip() for val in fields]

    return request.make_response(self.from_data(columns_headers, import_data),
                                 headers=[('Content-Disposition',
                                           content_disposition(self.filename(model))),
                                          ('Content-Type', self.content_type)],
                                 cookies={'fileToken': token})


ExportFormat.base = base
