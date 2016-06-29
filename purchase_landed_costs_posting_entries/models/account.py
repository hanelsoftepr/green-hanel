# __author__ = 'trananhdung'

from openerp import models, fields


class nppAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    origin = fields.Char(string='Origin')
