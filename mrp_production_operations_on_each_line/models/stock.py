# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from openerp import models, api, fields


class StockMoveExtend(models.Model):
    _inherit = 'stock.move'
