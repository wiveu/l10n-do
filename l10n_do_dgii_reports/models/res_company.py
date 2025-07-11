from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_do_is_subject_to_proportionality = fields.Boolean(
        string='Is Subject to Proportionality',
        help='Check this box if the company is subject to proportionality '
    )

    @api.model
    def create(self, vals):
        """Override to configure DGII taxes when creating Dominican company"""
        company = super().create(vals)
        
        # If this is a Dominican company, configure DGII taxes
        if company.country_id and company.country_id.code == 'DO':
            try:
                self.env['account.tax'].with_company(company)._configure_dgii_tax_types()
            except Exception:
                # Don't fail company creation if tax configuration fails
                pass
            
        return company
