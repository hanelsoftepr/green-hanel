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
    'depends': ['mrp', 'purchase'],
    'data': ['views/mrp_view.xml',
             'configs/mrp_config_data.xml'
             ],
    'installable': True,
    'price': 140,
    'currency': 'EUR',
    'auto_install': False,
    'application': False,
}
