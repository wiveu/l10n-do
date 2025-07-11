# DGII Reports - Dominican Republic

This module extends the functionalities of l10n_do_ncf, integrating fiscal declaration reports for compliance with Dominican Republic Internal Revenue Service (DGII) requirements.

## 📌 Description

The **DGII Reports** module for Odoo 18 enables Dominican companies to generate and manage the fiscal reports required by the Dominican Republic General Directorate of Internal Revenue (DGII). This module extends the base NCF (Número de Comprobante Fiscal) functionality to provide comprehensive reporting capabilities for tax compliance.

## ✅ Features

### 📊 Fiscal Reports Generation
- **IT-1 Report (IT1)**: Monthly report of sales and purchases with fiscal value
- **606 Report**: Monthly report of purchases and external services
- **607 Report**: Monthly report of sales
- **608 Report**: Report of cancellations
- **609 Report**: Report of external payments

### 🔄 Data Integration
- **Tax Type Classification**: Automatic classification of transactions by tax type
- **Invoice Service Type Details**: Detailed categorization of services for reporting
- **Withholding Management**: Support for tax withholdings and their proper reporting

### 📈 Advanced Filtering
- **Date Range Selection**: Generate reports for specific periods
- **Company Filter**: Multi-company support for consolidated reports
- **Transaction Type Filter**: Filter by specific transaction types
- **NCF Validation**: Ensure all transactions have valid fiscal numbers

### 🎯 Compliance Features
- **DGII Format Export**: Export reports in the exact format required by DGII
- **XML/TXT Generation**: Generate files in the official formats
- **Validation Rules**: Built-in validation to ensure data integrity
- **Error Reporting**: Identify and highlight compliance issues

### 📋 Additional Functionalities
- **Purchase Classification**: Automatic classification of purchases by type
- **Service Type Details**: Detailed service categorization for accurate reporting
- **Tax Configuration**: Pre-configured tax settings for Dominican Republic
- **Reconciliation Tools**: Tools to reconcile reported data with accounting records

## 🔧 Technical Features

### Models Extended
- `account.move`: Enhanced with DGII reporting fields
- `account.move.line`: Additional tax classification fields
- `res.partner`: Extended with fiscal classification data
- `account.tax`: Enhanced with DGII-specific configurations

### Data Files Included
- Invoice service type detail configurations
- Dominican Republic tax data
- DGII report templates and layouts
- Default configurations for fiscal compliance

## 📥 Requirements

- **Odoo Version**: 18.0+
- **Dependencies**:
  - `web`: Web interface functionality
  - `account`: Accounting module
  - `l10n_do`: Dominican Republic localization
  - `l10n_do_ncf`: NCF (Fiscal Number) management

## 🚀 Installation

1. Ensure all dependencies are installed
2. Copy the module to your Odoo addons directory
3. Update the application list from Apps menu
4. Install the "DGII Reports" module

## 💼 Usage

### Generating DGII Reports

1. Navigate to **Accounting > Reporting > DGII Reports**
2. Select the desired report type (606, 607, 608, 609, IT-1)
3. Choose the reporting period (month/year)
4. Apply any additional filters if needed
5. Generate and download the report in DGII format

### Configuring Tax Classifications

1. Go to **Accounting > Configuration > Taxes**
2. Configure each tax with the appropriate DGII classification
3. Ensure proper mapping for purchase and sale transactions

### Setting Up Service Types

1. Navigate to **Accounting > Configuration > Invoice Service Types**
2. Configure service type details as required by DGII
3. Map services to the appropriate categories

## 🔍 Validation and Compliance

The module includes built-in validations to ensure:
- All invoices have valid NCF numbers
- Proper tax classification for all transactions
- Correct partner fiscal information
- Compliance with DGII reporting format requirements

## 📞 Support

- **Version**: 18.0.1.4.9
- **License**: LGPL-3
- **Authors**: Indexa SRL, Iterativo SRL, Jenrax SRL, Neotec
- **Website**: https://github.com/Jenrax-git/l10n-do

For technical support or customizations, please contact the development team.
