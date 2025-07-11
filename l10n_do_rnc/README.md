# Search RNC Name - Dominican Tax ID Lookup

This module searches for company names by entering a Taxpayer Registration Number (RNC), validating company information through official Dominican Republic services.

## 📌 Description

The **Search RNC Name** module for Odoo 18 provides automatic company information retrieval using the Dominican Republic Taxpayer Registration Number (RNC). This module integrates with official DGII services to validate and automatically populate partner information, ensuring accurate and up-to-date business data.

## ✅ Features

### 🔍 RNC Lookup Functionality
- **Automatic Name Search**: Retrieve company names using RNC
- **Real-time Validation**: Validate RNC format and existence
- **DGII Integration**: Direct integration with official DGII services
- **Data Auto-completion**: Automatically populate partner information

### 🏢 Partner Information Management
- **Company Validation**: Verify if RNC belongs to a valid company
- **Business Status**: Check if company is active or inactive
- **Contact Information**: Retrieve available contact details
- **Address Lookup**: Get registered business addresses when available

### ⚙️ Service Configuration
- **Multiple Providers**: Support for different RNC lookup services
- **Service Selection**: Choose between DGII and alternative providers
- **Fallback Options**: Automatic fallback to alternative services
- **Custom API Integration**: Support for custom RNC lookup APIs

### 🔄 Integration Features
- **Contact Module**: Seamless integration with Odoo contacts
- **NCF Module**: Integration with fiscal documentation
- **VAT Validation**: Enhanced VAT validation with RNC lookup
- **Base Localization**: Works with Dominican Republic base localization

## 🔧 Technical Features

### Service Providers
- **DGII Official**: Direct integration with official DGII services
- **Third-party APIs**: Support for alternative RNC lookup services
- **Custom Services**: Ability to integrate custom lookup services
- **Service Monitoring**: Track service availability and performance

### Data Validation
- **RNC Format**: Validate RNC format (9 or 11 digits)
- **Checksum Validation**: Verify RNC checksum calculations
- **Business Type**: Identify business type from RNC structure
- **Status Verification**: Check active/inactive status

### User Interface
- **Search Button**: One-click RNC lookup from partner form
- **Progress Indicators**: Visual feedback during lookup process
- **Error Messages**: Clear error messages for lookup failures
- **Success Notifications**: Confirmation when data is found

## 📥 Requirements

- **Odoo Version**: 18.0+
- **Dependencies**:
  - `base`: Odoo core functionality
  - `contacts`: Contact management
  - `l10n_do`: Dominican Republic localization
  - `l10n_do_ncf`: NCF management (optional but recommended)
  - `base_vat`: VAT validation framework

## 🚀 Installation

1. Ensure all dependencies are installed
2. Copy this module to your Odoo addons directory
3. Update the application list
4. Install the "Search RNC Name" module
5. Configure RNC lookup service settings

## 💼 Usage

### Configuration

1. **Service Setup**:
   - Go to Settings > General Settings
   - Find "RNC Service" section
   - Select your preferred RNC lookup service
   - Configure API credentials if required

2. **Service Selection**:
   - **DGII**: Official Dominican government service
   - **Alternative Services**: Third-party providers
   - Test the selected service to ensure it's working

### Using RNC Lookup

1. **Creating New Partners**:
   - Create a new contact (customer/supplier)
   - Enter the RNC in the "Tax ID" field
   - Click the "Search RNC" button
   - Review and confirm the retrieved information

2. **Updating Existing Partners**:
   - Open an existing partner record
   - Modify or enter the RNC
   - Use the search function to update information
   - Compare existing data with retrieved data

3. **Validation Process**:
   - The system validates RNC format automatically
   - Real-time lookup retrieves company information
   - Data is populated in the partner form
   - User can review and modify before saving

### Batch Operations

1. **Multiple Lookups**:
   - Use the partner list view
   - Select multiple partners with RNC
   - Use batch actions to lookup information
   - Review results and apply changes

## 🔍 RNC Format Validation

### Supported Formats
- **9-digit RNC**: Standard company registration numbers
- **11-digit RNC**: Enhanced format with additional validation
- **Cedula**: Personal identification numbers (9 digits)
- **Special Cases**: Government and institutional numbers

### Validation Rules
- **Format Check**: Verify digit count and structure
- **Checksum**: Validate mathematical checksum
- **Prefix Validation**: Check valid RNC prefixes
- **Status Verification**: Confirm active status with DGII

## ⚙️ Configuration Options

### Service Settings
- **Primary Service**: Choose main RNC lookup provider
- **Timeout Settings**: Configure service timeout limits
- **Retry Logic**: Set number of retry attempts
- **Cache Duration**: Configure how long to cache results

### Data Handling
- **Auto-populate**: Automatically fill partner fields
- **Data Overwrite**: Choose whether to overwrite existing data
- **Field Mapping**: Configure which fields to populate
- **Validation Level**: Set validation strictness

### Error Handling
- **Fallback Services**: Configure alternative services
- **Error Logging**: Log failed lookup attempts
- **User Notifications**: Configure error message display
- **Retry Options**: Automatic retry on failures

## 🛡️ Security and Privacy

### Data Protection
- **Minimal Data**: Only retrieve necessary information
- **Secure Transmission**: Encrypted communication with services
- **Local Caching**: Secure local storage of lookup results
- **Access Control**: Role-based access to lookup functions

### Compliance
- **GDPR Compliance**: Respect data protection regulations
- **Local Law**: Comply with Dominican Republic data laws
- **Service ToS**: Respect third-party service terms of service
- **Audit Trail**: Log all lookup activities

## 🔧 Troubleshooting

### Common Issues
1. **Service Unavailable**: Check internet connection and service status
2. **Invalid RNC**: Verify RNC format and validity
3. **No Results Found**: RNC may not exist in service database
4. **Timeout Errors**: Increase timeout settings or try alternative service

### Diagnostic Tools
- **Service Test**: Built-in service connectivity test
- **Lookup History**: Review previous lookup attempts
- **Error Logs**: Detailed error logging for troubleshooting
- **Performance Metrics**: Monitor lookup response times

## 📞 Support

- **Version**: 18.0.1.1.1
- **License**: LGPL-3
- **Authors**: Guavana, Jenrax SRL
- **Website**: https://github.com/Jenrax-git/l10n-do

For technical support, service configuration assistance, or custom integrations, please contact the development team.
