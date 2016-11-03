{
    'name': 'Purchase Landed Cost - Assigning before Receiving',
    'summary': 'Assigning Purchase Landed Cost for Incoming Shipment before receiving',
    'version': '1.0',
    'category': 'Purchase',
    'description': """
    """,
    'author': "Hanel Software Solutions",
    'website': 'http://www.hanelsoft.vn/',
    'depends': ['purchase_landed_costs_posting_entries'],
    'data': ['views/views.xml',
             'views/res_partner_view.xml',
             'wizard/reposting_view.xml'],
    'price': 79.50,
    'currency': 'EUR',
    'installable': False,
    'auto_install': False,
    'application': False,
}
