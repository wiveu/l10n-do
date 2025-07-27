# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>
# © 2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Eneldo Serrata <eneldo@marcos.do>

{
    'name': "DGII Reports",

    'summary': """
        This module extends the functionalities of l10n_do_ncf,
        integrating fiscal declaration reports""",

    'author': "Indexa, SRL, Iterativo SRL, Jenrax SRL, Neotec",
    'license': 'LGPL-3',
    "category": "Localization",
    'countries': ['do'],
    'version': '18.0.1.5.1',
    'website': "https://github.com/Jenrax-git/l10n-do",
    # any module necessary for this one to work correctly
    'depends': [
        'web',
        'account',
        'l10n_do',
        'l10n_do_ncf'
    ],
    # always loaded
    'data': [
        'data/invoice_service_type_detail_data.xml',
        'data/action_server.xml',

        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/res_partner_views.xml',
        'views/account_account_views.xml',
        'views/account_move_views.xml',
        'views/dgii_report_views.xml',
        'views/account_tax_views.xml',
        'views/res_config_settings_views.xml',

        'wizard/dgii_report_regenerate_wizard_views.xml',
    ],

    'assets':{
        'web.assets_backend': [
            # TODO: This not working repair and here for repair
            # 'l10n_do_dgii_reports/static/src/scss/dgii_reports.scss',
            # 'l10n_do_dgii_reports/static/src/js/widget.js',
        ]
    },

    'post_init_hook': 'post_install_hook',
    'uninstall_hook': 'uninstall_hook',

}
