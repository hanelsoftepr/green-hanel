__author__ = 'trananhdung'

from openerp import models, fields



class npp_res_partner(models.Model):
    _inherit = 'res.partner'

    landed_cost = fields.Boolean(string='Landed Cost')
