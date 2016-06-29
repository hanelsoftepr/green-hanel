__author__ = 'trananhdung'

from openerp import fields, models, api
from openerp.osv import fields as osvFields
from openerp.exceptions import ValidationError


class nppStockPicking(models.Model):
    _inherit = 'stock.picking'

    # @api.multi
    # @api.depends('move_lines', 'landed_cost', 'expense_ids')
    # def _picking_state_get(self):
    #     '''The state of a picking depends on the state of its related stock.move
    #         draft: the picking has no line or any one of the lines is draft
    #         done, draft, cancel: all lines are done / draft / cancel
    #         confirmed, waiting, assigned, partially_available depends on move_type (all at once or partial)
    #     '''
    #     for pick in self:
    #         state = ''
    #         if (not pick.move_lines) or any([x.state in ['draft', False] for x in pick.move_lines]):
    #             pick.state = 'draft'
    #             continue
    #         if all([x.state == 'cancel' for x in pick.move_lines]):
    #             pick.state = 'cancel'
    #             continue
    #         if all([x.state in ('cancel', 'done', 'delivered') for x in pick.move_lines]):
    #             pick.state = 'done'
    #             continue
    #
    #         order = {'confirmed': 0, 'waiting': 1, 'assigned': 2}
    #         order_inv = {0: 'confirmed', 1: 'waiting', 2: 'assigned'}
    #         lst = [order[x.state] for x in pick.move_lines if x.state not in ('cancel', 'done', 'delivered')]
    #         if pick.move_type == 'one':
    #             state = order_inv[min(lst)]
    #         else:
    #             # we are in the case of partial delivery, so if all move are assigned, picking
    #             # should be assign too, else if one of the move is assigned, or partially available, picking should be
    #             # in partially available state, otherwise, picking is in waiting or confirmed state
    #             state = order_inv[max(lst)]
    #             if not all(x == 2 for x in lst):
    #                 if any(x == 2 for x in lst):
    #                     state = 'partially_available'
    #                 else:
    #                     # if all moves aren't assigned, check if we have one product partially available
    #                     for move in pick.move_lines:
    #                         if move.partially_available:
    #                             state = 'partially_available'
    #                             break
    #         if state == 'assigned' and pick.landed_cost and \
    #                 not (pick.expense_ids or (pick.distribution_id and pick.cost_line_ids)):
    #             state = 'landed_cost'
    #         pick.state = state

    @api.multi
    def _state_get(self, field_name, arg, context=None):
        '''The state of a picking depends on the state of its related stock.move
            draft: the picking has no line or any one of the lines is draft
            done, draft, cancel: all lines are done / draft / cancel
            confirmed, waiting, assigned, partially_available depends on move_type (all at once or partial)
        '''
        res = {}
        for pick in self:
            if (not pick.move_lines) or any([x.state == 'draft' for x in pick.move_lines]):
                res[pick.id] = 'draft'
                continue
            if all([x.state == 'cancel' for x in pick.move_lines]):
                res[pick.id] = 'cancel'
                continue
            if all([x.state in ('cancel', 'done', 'delivered') for x in pick.move_lines]):
                res[pick.id] = 'done'
                continue

            order = {'confirmed': 0, 'waiting': 1, 'assigned': 2}
            order_inv = {0: 'confirmed', 1: 'waiting', 2: 'assigned'}
            lst = [order[x.state] for x in pick.move_lines if x.state not in ('cancel', 'done')]
            if pick.move_type == 'one':
                res[pick.id] = order_inv[min(lst)]
            else:
                # we are in the case of partial delivery, so if all move are assigned, picking
                # should be assign too, else if one of the move is assigned, or partially available, picking should be
                # in partially available state, otherwise, picking is in waiting or confirmed state
                res[pick.id] = order_inv[max(lst)]
                if not all(x == 2 for x in lst):
                    if any(x == 2 for x in lst):
                        res[pick.id] = 'partially_available'
                    else:
                        # if all moves aren't assigned, check if we have one product partially available
                        for move in pick.move_lines:
                            if move.partially_available:
                                res[pick.id] = 'partially_available'
                                break
            if res[pick.id] == 'assigned' and pick.landed_cost and \
                    not (pick.expense_ids or (pick.distribution_id and pick.cost_line_ids)):
                res[pick.id] = 'landed_cost'
        return res

    @api.multi
    def _get_pickings(self):
        res = set()
        for r in self:
            if r.picking_id:
                res.add(r.picking_id.id)
        return list(res)
    _columns = {
        'state': osvFields.function(
            _state_get, type="selection", copy=False,
            store={
                'stock.picking': (lambda self, cr, uid, ids, ctx: ids,
                                  ['move_type', 'landed_cost', 'distribution_id'], 20),
                'stock.move': (_get_pickings, ['state', 'picking_id', 'partially_available'], 20),
                'purchase.cost.distribution.expense': (_get_pickings, ['picking_id'], 20),
                'purchase.cost.distribution.line': (_get_pickings, ['picking_id'], 20)
            },
            selection=[
                ('draft', 'Draft'),
                ('cancel', 'Cancelled'),
                ('waiting', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('partially_available', 'Partially Available'),
                ('landed_cost', 'Waiting for Landed Cost'),
                ('assigned', 'Ready to Transfer'),
                ('done', 'Transferred'),
                ], string='Status', readonly=True, select=True, track_visibility='onchange',
            help="""
                * Draft: not confirmed yet and will not be scheduled until confirmed\n
                * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                * Waiting Availability: still waiting for the availability of products\n
                * Partially Available: some products are available and reserved\n
                * Ready to Transfer: products reserved, simply waiting for confirmation.\n
                * Transferred: has been processed, can't be modified or cancelled anymore\n
                * Cancelled: has been cancelled, can't be confirmed anymore"""
        )
    }
    expense_ids = fields.One2many(
        comodel_name='purchase.cost.distribution.expense',
        inverse_name='picking_id',
        string='Expenses'
    )
    cost_line_ids = fields.One2many(
        comodel_name='purchase.cost.distribution.line',
        inverse_name='picking_id',
        string='Cost Lines'
    )
    distribution_id = fields.Many2one(comodel_name='purchase.cost.distribution',
                                      string='Purchase Cost Distribution')
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        help='Account Journal for posting landed to Journal Entry'
    )
    # state = fields.Selection(selection=[('draft', 'Draft'),
    #                                     ('cancel', 'Cancelled'),
    #                                     ('waiting', 'Waiting Another Operation'),
    #                                     ('confirmed', 'Waiting Availability'),
    #                                     ('partially_available', 'Partially Available'),
    #                                     ('landed_cost', 'Waiting for Landed Cost'),
    #                                     ('assigned', 'Ready for Picking'),
    #                                     ('done', 'Transferred')],
    #                          string='Status', compute='_picking_state_get',
    #                          store=True, readonly=True)
    landed_cost = fields.Boolean(string='Landed Cost', copy=False)

    @api.multi
    def action_done(self):
        self.write({'landed_cost': False})
        res = super(nppStockPicking, self).action_done()
        # self._recompute_state()
        return res

    @api.multi
    def _recompute_state(self):
        self.env.all.todo.update({self._fields['state']: [r for r in self]})
        self.recompute()


class nppStockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        res = super(nppStockTransferDetails, self).do_detailed_transfer()
        PurchaseCostDistributionModel = self.env['purchase.cost.distribution']
        incomingShipment = self.picking_id
        if incomingShipment.distribution_id:
            incomingShipment.distribution_id.action_calculate()
            incomingShipment.distribution_id.with_context(
                forPickingID=incomingShipment.id).action_done()
            return res
        if self.picking_id.expense_ids:
            if not self.picking_id.journal_id:
                raise ValidationError('This Incoming Shipment is not set Account Journal!')
            PCD = PurchaseCostDistributionModel.create(
                {
                    'account_journal_id': incomingShipment.journal_id.id,
                    'expense_lines': [(6, 0, [x.id for x in incomingShipment.expense_ids])]
                }
            )
            partner = incomingShipment.partner_id
            pickImportWizard = self.env['picking.import.wizard'].with_context(
                active_id=PCD.id,
                active_model='purchase.cost.distribution'
            ).create(
                {
                    'supplier': partner.id,
                    'pickings': [[6, False, [incomingShipment.id]]]
                }
            )
            pickImportWizard.with_context(
                active_id=PCD.id,
                active_model='purchase.cost.distribution'
            ).action_import_picking()
            PCD.action_calculate()
            PCD.action_done()
        return res

