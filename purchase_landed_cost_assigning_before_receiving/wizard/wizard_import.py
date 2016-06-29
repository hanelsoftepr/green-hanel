__author__ = 'trananhdung'

from openerp import models, fields, api


class extendPickingImportWizard(models.TransientModel):
    _inherit = 'picking.import.wizard'

    pickings = fields.Many2many(
        comodel_name='stock.picking',
        relation='distribution_import_picking_rel', column1='wizard_id',
        column2='picking_id', string='Incoming shipments',
        domain="[('partner_id', 'child_of', supplier),"
               "('location_id.usage', '=', 'supplier'),"
               "('id', 'not in', prev_pickings[0][2]),"
               "('state', 'in', ('landed_cost','done'))]", required=True)

    @api.multi
    def action_import_picking(self):
        self.ensure_one()
        # for picking in self.pickings:
        #     for move in picking.move_lines:
        #         self.env['purchase.cost.distribution.line'].create(
        #             self._prepare_distribution_line(move))
        self.pickings.write({
            'distribution_id': self.env.context.get('active_id', False)
        })
        return super(extendPickingImportWizard, self).action_import_picking()
