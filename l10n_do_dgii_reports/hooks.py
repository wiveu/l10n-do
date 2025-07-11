from odoo import SUPERUSER_ID, api


def post_install_hook(cr, registry):
    """Configure DGII tax types after module installation"""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Find all companies with Dominican localization
        companies = env['res.company'].search([
            ('country_id.code', '=', 'DO')
        ])
        
        for company in companies:
            # Switch to company context and configure taxes
            company_env = env['account.tax'].with_company(company)
            try:
                company_env._configure_dgii_tax_types()
            except Exception as e:
                # Log error but don't fail installation
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning("Could not configure DGII tax types for company %s: %s", company.name, str(e))


def uninstall_hook(cr, registry):
    """Clean up DGII tax types when module is uninstalled"""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        try:
            # Reset DGII fields to default values
            taxes = env['account.tax'].search([
                ('l10n_do_tax_type', '!=', 'none')
            ])
            
            taxes.write({
                'l10n_do_tax_type': 'none',
                'isr_retention_type': False
            })
        except Exception:
            # Ignore errors during uninstallation
            pass
