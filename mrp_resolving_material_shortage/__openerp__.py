{
    'name': 'Manufacturing - Stock Operations',
    'summary': 'Auto resolve shortage of Raw Materials by Internal Transfer or Procurement Order',
    'version': '1.0',
    'category': 'Manufacturing',
    'description': """
        Auto resolve shortage of Raw Materials by Internal Transfer or Procurement Order
    """,
    'author': "Hanel Software Solutions",
    'website': 'http://www.hanelsoft.vn/',
    'depends': ['mrp'],
    'data': ['views/product_view.xml',
             'views/mrp_view.xml',
             'views/stock_view.xml',
             'configs/mrp_config_data.xml'
             ],
    'installable': True,
    'price': 120,
    'currency': 'EUR',
    'auto_install': False,
    'application': False,
}
