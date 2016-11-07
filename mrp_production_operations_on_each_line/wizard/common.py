__author__ = 'trananhdung'


def _commonCalculateQty(cls, production=False, moves=False):
    if not (production or moves):
        return []
    if production:
        moves = production.move_lines
    quantModel = cls.env['stock.quant']
    toConsumeDetails = {}
    for move in moves:
        if move.state not in ('assigned', 'confirmed', 'waiting'):
            continue
        product_id = move.product_id.id
        quants = quantModel.quants_get_prefered_domain(
                move.location_id, move.product_id, move.product_qty,
                domain=[('qty', '>', 0.0), ('reservation_id', '=', move.id)],
                prefered_domain_list=[]
            )
        # quants = move.reserved_quant_ids
        if product_id not in toConsumeDetails:
            toConsumeDetails[product_id] = {}
        consumeLines = toConsumeDetails[product_id]
        for quant in quants:
            product_qty = quant[0].qty if quant[0] is not None else quant[1]
            lot_id = quant[0].lot_id.id if quant[0] is not None else False
            if lot_id in consumeLines:
                consumeLines[lot_id] += product_qty
            else:
                consumeLines[lot_id] = product_qty

    result = []
    for product_id in toConsumeDetails:
        for lotID in toConsumeDetails[product_id]:
            result.append({
                'product_id': product_id,
                'lot_id': lotID,
                'product_qty': toConsumeDetails[product_id][lotID]
            })
    return result
