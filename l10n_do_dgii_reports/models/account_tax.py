from odoo import models, fields, api
from odoo.tools import config


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_do_tax_type = fields.Selection(
        selection=[
            ('itbis', 'ITBIS'),
            ('ritbis', 'ITBIS Withholding'),
            # TODO: investigate Subject to proportionality and ITBIS carried to cost
            #('prop', 'Subject to proportionality'),
            #('itbis_cost', 'ITBIS carried to cost'),
            ('isr', 'ISR Withholding'),
            ('isc', 'Selective Consumption Tax (SCT)'),
            ('other', 'Other taxes'),
            ('tip', 'Legal tip'),
            ('rext', 'Overseas payments (law 253-12)'),
            ('none', 'Non deductible')
        ],
        default="none",
        string="Tax DGII Type",
    )
    isr_retention_type = fields.Selection(
        selection=[
            ('01', 'Rentals'),
            ('02', 'Fees for Services'),
            ('03', 'Other Incomes'),
            ('04', 'Presumed Income'),
            ('05', 'Interest Paid to Legal Entities'),
            ('06', 'Interests Paid to Individuals'),
            ('07', 'Withholding by State Providers'),
            ('08', 'Mobile Games')
        ],
        string="ISR Withholding Type",
    )

    @api.model
    def _configure_dgii_tax_types(self):
        """Configure DGII tax types for Dominican taxes"""
        # Mapping of tax external IDs to their DGII configuration
        dgii_config = {
            # Sales taxes
            'l10n_do.tax_0_sale': {'l10n_do_tax_type': 'none'},
            'l10n_do.tax_18_sale': {'l10n_do_tax_type': 'itbis'},
            'l10n_do.tax_tip_sale': {'l10n_do_tax_type': 'tip'},
            'l10n_do.tax_18_of_10': {'l10n_do_tax_type': 'itbis'},
            
            # Purchase taxes
            'l10n_do.tax_0_purch': {'l10n_do_tax_type': 'none'},
            'l10n_do.tax_18_purch': {'l10n_do_tax_type': 'itbis'},
            'l10n_do.tax_16_purch': {'l10n_do_tax_type': 'itbis'},
            'l10n_do.tax_9_purch': {'l10n_do_tax_type': 'itbis'},
            'l10n_do.tax_8_purch': {'l10n_do_tax_type': 'itbis'},
            'l10n_do.tax_tip_purch': {'l10n_do_tax_type': 'tip'},
            'l10n_do.tax_18_purch_serv': {'l10n_do_tax_type': 'itbis'},
            'l10n_do.tax_18_importation': {'l10n_do_tax_type': 'itbis'},
            
            # Other taxes
            'l10n_do.tax_0015_bank': {'l10n_do_tax_type': 'other'},
            'l10n_do.tax_10_telco': {'l10n_do_tax_type': 'isc'},
            'l10n_do.tax_2_telco': {'l10n_do_tax_type': 'other'},
            
            # Retention taxes
            'l10n_do.ret_100_tax_security': {'l10n_do_tax_type': 'ritbis'},
            'l10n_do.ret_100_tax_nonprofit': {'l10n_do_tax_type': 'ritbis'},
            'l10n_do.ret_100_tax_person': {'l10n_do_tax_type': 'ritbis'},
            'l10n_do.ret_30_tax_moral': {'l10n_do_tax_type': 'ritbis'},
            'l10n_do.ret_30_tax_freelance': {'l10n_do_tax_type': 'ritbis'},
            'l10n_do.ret_75_tax_nonformal': {'l10n_do_tax_type': 'ritbis'},
            
            # Income retention taxes with ISR types
            'l10n_do.ret_10_income_person': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '02'},
            'l10n_do.ret_10_income_rent': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '01'},
            'l10n_do.ret_10_income_dividend': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
            'l10n_do.ret_2_income_person': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
            'l10n_do.ret_2_income_transfer': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
            'l10n_do.ret_27_income_remittance': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '03'},
            'l10n_do.ret_5_income_gov': {'l10n_do_tax_type': 'isr', 'isr_retention_type': '07'},
        }
        
        # Also try to find taxes by name patterns if external IDs don't work
        name_patterns = {
            # ITBIS taxes
            ('18%', 'sale'): 'itbis',
            ('18%', 'purchase'): 'itbis',
            ('16%', 'purchase'): 'itbis',
            ('9%', 'purchase'): 'itbis',
            ('8%', 'purchase'): 'itbis',
            ('0%', 'exempt'): 'none',
            
            # Tip taxes
            ('propina', 'tip'): 'tip',
            ('10%', 'propina'): 'tip',
            
            # Other patterns
            ('0.15%', 'bank'): 'other',
            ('telco', '10%'): 'isc',
            ('telco', '2%'): 'other',
        }
        
        # Try to configure using external IDs first
        for external_id, config_values in dgii_config.items():
            try:
                tax = self.env.ref(external_id, raise_if_not_found=False)
                if tax:
                    tax.write(config_values)
            except Exception:
                # If tax doesn't exist, skip it
                continue
        
        # Fallback: configure by name patterns for existing taxes
        all_taxes = self.search([('company_id', '=', self.env.company.id)])
        for tax in all_taxes:
            tax_name = tax.name.lower()
            tax_description = (tax.description or '').lower()
            
            # Check for ITBIS taxes
            if any(pattern in tax_name for pattern in ['18%', '16%', '9%', '8%']) and 'itbis' in tax_name:
                if not tax.l10n_do_tax_type or tax.l10n_do_tax_type == 'none':
                    tax.l10n_do_tax_type = 'itbis'
            
            # Check for tip taxes
            elif 'propina' in tax_name or 'tip' in tax_name:
                if not tax.l10n_do_tax_type or tax.l10n_do_tax_type == 'none':
                    tax.l10n_do_tax_type = 'tip'
            
            # Check for exempt taxes
            elif any(pattern in tax_name for pattern in ['exempt', 'exento', '0%']) and 'itbis' in tax_name:
                tax.l10n_do_tax_type = 'none'
            
            # Check for retention taxes
            elif any(pattern in tax_name for pattern in ['ret', 'retention', 'withhold']):
                if 'itbis' in tax_name:
                    tax.l10n_do_tax_type = 'ritbis'
                elif 'isr' in tax_name or 'income' in tax_name:
                    tax.l10n_do_tax_type = 'isr'
                    # Set ISR retention type based on name patterns
                    if 'rent' in tax_name:
                        tax.isr_retention_type = '01'
                    elif any(pattern in tax_name for pattern in ['service', 'fee', 'person']):
                        tax.isr_retention_type = '02'
                    elif any(pattern in tax_name for pattern in ['gov', 'government', 'state']):
                        tax.isr_retention_type = '07'
                    else:
                        tax.isr_retention_type = '03'  # Default to "Other Incomes"
