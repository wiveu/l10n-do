# Fiscal POS (Rep. Dominicana) - Point of Sale NCF Integration

This module incorporates NCF (Número de Comprobante Fiscal) billing functionalities to the Point of Sale system for Dominican Republic compliance.

## 📌 Description

The **Fiscal POS** module for Odoo 18 extends the Point of Sale functionality to support Dominican Republic fiscal requirements. It enables the generation of fiscal receipts with proper NCF numbering directly from the POS interface, ensuring compliance with DGII regulations for retail operations.

## ✅ Features

### 🧾 NCF Integration in POS
- **Automatic NCF Assignment**: Automatic generation of fiscal numbers for POS orders
- **Real-time Validation**: Instant validation of NCF format and sequence
- **Receipt Printing**: Fiscal-compliant receipt printing with NCF
- **Multiple NCF Types**: Support for consumer and fiscal credit invoices

### 🖥️ POS Interface Enhancements
- **Customer Selection**: Enhanced customer selection with fiscal information
- **NCF Display**: Clear display of assigned NCF in POS interface
- **Fiscal Status**: Visual indicators for fiscal compliance status
- **Error Handling**: User-friendly error messages for fiscal issues

### 💳 Payment Method Integration
- **Fiscal Payment Types**: Configuration of payment methods for fiscal compliance
- **Tax Calculation**: Proper tax calculation for fiscal receipts
- **Multi-currency**: Support for USD and DOP transactions
- **Payment Validation**: Validation of payment types against fiscal requirements

### 📊 Order Management
- **Fiscal Order Types**: Support for different fiscal order types
- **Customer Classification**: Automatic classification of customers (final consumer vs fiscal)
- **Tax Exemptions**: Handle tax-exempt transactions properly
- **Order Validation**: Pre-validation before order completion

### 🔄 Backend Integration
- **Accounting Sync**: Seamless synchronization with accounting module
- **NCF Sequence Management**: Integration with NCF sequence control
- **Journal Assignment**: Automatic journal assignment based on NCF type
- **Fiscal Reports**: POS transactions included in fiscal reports

## 🔧 Technical Features

### POS Session Management
- **Fiscal Session Control**: Enhanced session management with fiscal validation
- **Sequence Tracking**: Track NCF usage per session
- **Error Recovery**: Handle fiscal errors gracefully during sessions
- **Session Reports**: Include fiscal information in session reports

### User Interface Components
- **Custom Widgets**: Specialized widgets for fiscal information display
- **Responsive Design**: Mobile-friendly interface for tablet POS
- **Multi-language**: Support for Spanish and English interfaces
- **Accessibility**: Keyboard shortcuts for fiscal operations

### Data Models Enhanced
- `pos.order`: Extended with NCF and fiscal fields
- `pos.session`: Enhanced with fiscal session management
- `pos.payment.method`: Extended with fiscal payment classifications
- `pos.config`: Enhanced with fiscal configuration options

## 📥 Requirements

- **Odoo Version**: 18.0+
- **Dependencies**:
  - `base`: Odoo core functionality
  - `point_of_sale`: Point of Sale module
  - `l10n_do_ncf`: Dominican Republic NCF management

## 🚀 Installation

1. Ensure the NCF module (`l10n_do_ncf`) is installed and configured
2. Copy this module to your Odoo addons directory
3. Update the application list
4. Install the "Fiscal POS (Rep. Dominicana)" module
5. Configure POS settings for fiscal operations

## 💼 Usage

### POS Configuration

1. **Fiscal POS Setup**:
   - Enable fiscal mode in POS configuration
   - Configure NCF sequences for POS journals
   - Set default customer for final consumer transactions
   - Configure fiscal payment methods

2. **NCF Sequence Configuration**:
   - Assign consumer invoice sequences (NCF 02)
   - Configure fiscal credit sequences (NCF 01) for business customers
   - Set up sequence limits and expiration dates
   - Test sequence generation

3. **Payment Method Setup**:
   - Configure cash payment methods
   - Set up card payment integration
   - Configure fiscal classifications for each payment type
   - Test payment processing

### Daily Operations

1. **Starting a POS Session**:
   - Validate NCF sequences are available
   - Verify fiscal configuration
   - Open session with fiscal mode enabled

2. **Processing Sales**:
   - Select products and add to cart
   - Choose customer (final consumer or business)
   - Automatic NCF assignment based on customer type
   - Process payment and print fiscal receipt

3. **Handling Business Customers**:
   - Search and select registered business customers
   - Automatic assignment of fiscal credit NCF (01)
   - Include RNC information in receipt
   - Validate tax calculations

4. **Managing Returns and Refunds**:
   - Process returns with proper NCF cancellation
   - Generate credit notes when required
   - Maintain fiscal compliance for return transactions

### End of Day Procedures

1. **Session Closing**:
   - Review fiscal transaction summary
   - Validate NCF sequence usage
   - Generate fiscal session report
   - Close session with fiscal validation

2. **Reporting**:
   - Export fiscal data for DGII reports
   - Review transaction logs
   - Validate data integrity

## 🔍 Fiscal Compliance Features

### NCF Validation
- **Format Checking**: Validate NCF structure and format
- **Sequence Control**: Ensure sequential numbering
- **Expiration Monitoring**: Track sequence expiration dates
- **Duplicate Prevention**: Prevent duplicate NCF assignment

### Tax Management
- **ITBIS Calculation**: Proper calculation of Dominican sales tax
- **Tax Exemptions**: Handle tax-exempt transactions
- **Withholding Support**: Support for tax withholdings when applicable
- **Multi-rate Taxes**: Support for different tax rates

### Customer Classification
- **Final Consumer**: Default classification for walk-in customers
- **Business Customer**: Registered businesses with RNC
- **Government**: Special handling for government entities
- **Export**: Support for export transactions

## ⚙️ Configuration Options

### POS Settings
- **Fiscal Mode**: Enable/disable fiscal functionality
- **Default Customer**: Set default customer for final consumer sales
- **NCF Validation**: Configure validation strictness
- **Receipt Format**: Customize fiscal receipt layout

### Payment Methods
- **Fiscal Classification**: Classify payment methods for reporting
- **Tax Handling**: Configure tax treatment per payment method
- **Foreign Currency**: Handle USD payments with proper conversion

## 🎯 Best Practices

1. **Regular Sequence Monitoring**: Check NCF sequence availability daily
2. **Customer Data Quality**: Maintain accurate customer fiscal information
3. **Session Management**: Close sessions properly to maintain fiscal integrity
4. **Backup Procedures**: Regular backup of fiscal transaction data
5. **Staff Training**: Ensure staff understands fiscal requirements

## 📞 Support

- **Version**: 18.0.2.3.7
- **License**: LGPL-3
- **Authors**: Guavana, Indexa, Iterativo SRL, Neotec, Jenrax SRL
- **Website**: https://github.com/Jenrax-git/l10n-do

For technical support, customizations, or staff training, please contact the development team.
