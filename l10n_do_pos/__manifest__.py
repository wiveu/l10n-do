{
    'name': "Fiscal POS (Rep. Dominicana)",
    'summary': """Incorporates NCF billing functionalities to POS.""",
    'author': "Guavana, Indexa, Iterativo SRL, Neotec, Jenrax SRL",
    'license': 'LGPL-3',
    'website': "https://github.com/Jenrax-git/l10n-do",
    'category': 'Localization',
    'countries': ['do'],
    'version': '18.0.2.3.9',
    'depends': [
        'base',
        'point_of_sale',
        'l10n_do_ncf',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/data.xml',
        'views/res_config_settings_views.xml',
        'views/pos_order_views.xml',
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'l10n_do_pos/static/src/scss/*',
            'l10n_do_pos/static/src/js/*.js',
            'l10n_do_pos/static/src/overrides/**/*.js',
            'l10n_do_pos/static/src/xml/*.xml',
        ],
    },
    'installable': True,
}
