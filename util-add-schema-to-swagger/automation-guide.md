# Schema Automation Guide

This guide explains how to use the automated scripts to convert XML schemas to JSON schemas and apply comprehensive validation to Swagger/OpenAPI files.

## Overview

The automation suite consists of three main scripts with enhanced capabilities:

1. **`xsd-to-json-schema.py`** - Converts XML Schema (XSD) to JSON Schema with pattern fixes
2. **`apply-schema-to-swagger.py`** - Applies schema validation with case-insensitive matching
3. **`batch-enhance-apis.py`** - Processes multiple API files with progress reporting

## Recent Enhancements (January 2026)

### ✅ Case-Insensitive Schema Matching
- Handles field name variations between Swagger and schema files
- Example: "SupConfirm" in Swagger matches "Supconfirm" in JSON schema
- More reliable validation application across different file formats

### ✅ Pattern Conversion Fixes
- Fixed double-escaping issues in regex patterns
- Corrected alternation anchoring for proper validation
- Auto-grouping for alternation patterns

### ✅ Documentation Preservation
- Preserves `externalDocs`, `example`, and `description` metadata
- Applies validation while maintaining compliance documentation
- No synthetic descriptions override existing content

## Prerequisites

### Python Installation

Ensure Python 3.8+ is installed:

```bash
python --version  # Should show Python 3.8 or higher
```

### Install Required Packages

```bash
# Install all required dependencies
pip install -r requirements.txt

# Or install individually
pip install xmlschema jsonschema pyyaml requests click tqdm colorama
```

### Verify Installation

```bash
# Test the scripts are working
python xsd-to-json-schema.py --help
python apply-schema-to-swagger.py --help
python batch-enhance-apis.py --help
```

## Script 1: XSD to JSON Schema Conversion

### Basic Usage

```bash
# Convert XML schema to JSON schema
python xsd-to-json-schema.py xml-schema.xsd output-schema.json
```

### Advanced Usage

```bash
# Specify JSON Schema draft version
python xsd-to-json-schema.py xml-schema.xsd output-schema.json --draft-version 7

# Enable verbose output
python xsd-to-json-schema.py xml-schema.xsd output-schema.json --verbose
```

### Example with REST Service Schema

```bash
# Convert REST Service XML schema
python xsd-to-json-schema.py ../shcema/xml-schema.xsd rest-service-json-schema.json --verbose
```

### Output Example

```
✅ Successfully converted ../shcema/xml-schema.xsd to rest-service-json-schema.json
📊 Generated 150 schema definitions

📈 Conversion Summary:
   Simple types: 45
   Complex types: 105
   Total definitions: 150
```

## Script 2: Apply Schema to Swagger

### Basic Usage

```bash
# Apply schema validation to a Swagger file
python apply-schema-to-swagger.py api.yaml schema.json enhanced-api.yaml
```

### Strict Mode (Recommended)

```bash
# Enable strict validation (additionalProperties: false)
python apply-schema-to-swagger.py api.yaml schema.json enhanced-api.yaml --strict
```

### Advanced Options

```bash
# Verbose output with backup
python apply-schema-to-swagger.py api.yaml schema.json enhanced-api.yaml --strict --verbose --backup
```

### Example with REST Service API

```bash
# Enhance order buy API
python apply-schema-to-swagger.py order-buy-api-v1.yaml xml-aligned-json-schema.json enhanced-order-buy-api-v1.yaml --strict --verbose
```

### Output Example

```
📖 Loaded Swagger file: order-buy-api-v1.yaml
📖 Loaded schema file: xml-aligned-json-schema.json
🔧 Strict mode: True
📋 Extracted 150 schema definitions

📊 Enhancement Summary:
   ✅ Enhanced component schemas with validation
   ✅ Added 15 base validation types
   ✅ Enhanced 8 existing schemas
   ✅ Applied field-level validations
   ✅ Added API-specific transaction type validation
   ✅ Enhanced error handling schemas
   ✅ Added comprehensive documentation

✅ Successfully enhanced order-buy-api-v1.yaml -> enhanced-order-buy-api-v1.yaml
```

## Script 3: Batch Processing

### Process Multiple APIs

```bash
# Enhance all APIs in a directory
python batch-enhance-apis.py ../UAT-20251202 xml-aligned-json-schema.json enhanced-apis --strict
```

### Dry Run (Preview)

```bash
# See what files would be processed without making changes
python batch-enhance-apis.py ../UAT-20251202 xml-aligned-json-schema.json enhanced-apis --dry-run
```

### Verbose Batch Processing

```bash
# Detailed output for each file
python batch-enhance-apis.py ../UAT-20251202 xml-aligned-json-schema.json enhanced-apis --strict --verbose
```

### Output Example

```
📁 Found 8 Swagger files in ../UAT-20251202

🔄 Enhancing 8 files...
✅ Enhanced: distributor-order-response-inquiry-api-v1.yaml
✅ Enhanced: order-buy-api-v1.yaml
✅ Enhanced: order-sell-api-v1.yaml
✅ Enhanced: order-switch-api-v1.yaml
✅ Enhanced: order-transfer-api-v1.yaml
✅ Enhanced: order-ict-api-v1.yaml
❌ Failed: malformed-api.yaml - Invalid YAML syntax
✅ Enhanced: manufacturer-order-response-api-v1.yaml

📊 Batch Enhancement Complete:
   ✅ Successful: 7
   ❌ Failed: 1
   📂 Output directory: enhanced-apis
```

## Complete Workflow Examples

### Scenario 1: Single API Enhancement

```bash
# Step 1: Convert XML schema (one-time)
python xsd-to-json-schema.py ../shcema/xml-schema.xsd rest-service-schema.json

# Step 2: Enhance a single API
python apply-schema-to-swagger.py my-api.yaml rest-service-schema.json enhanced-my-api.yaml --strict
```

### Scenario 2: Batch API Enhancement

```bash
# Step 1: Convert XML schema (one-time)
python xsd-to-json-schema.py ../shcema/xml-schema.xsd rest-service-schema.json --verbose

# Step 2: Preview what will be processed
python batch-enhance-apis.py ../UAT-20251202 rest-service-schema.json enhanced-apis --dry-run

# Step 3: Process all APIs
python batch-enhance-apis.py ../UAT-20251202 rest-service-schema.json enhanced-apis --strict --verbose
```

### Scenario 3: Continuous Integration

```bash
#!/bin/bash
# CI script for automatic enhancement

echo "🔄 Starting API enhancement pipeline..."

# Convert schema
if python xsd-to-json-schema.py schema/xml-schema.xsd build/rest-service-schema.json; then
    echo "✅ Schema conversion successful"
else
    echo "❌ Schema conversion failed"
    exit 1
fi

# Enhance APIs
if python batch-enhance-apis.py apis/ build/rest-service-schema.json enhanced-apis/ --strict; then
    echo "✅ API enhancement successful"
else
    echo "❌ API enhancement failed"
    exit 1
fi

echo "🎉 Pipeline completed successfully"
```

## Advanced Configuration

### Custom Type Mappings

You can modify the scripts to add custom field mappings:

```python
# In apply-schema-to-swagger.py, modify the field_mappings dict:
field_mappings = {
    'Date': 'Date8',
    'Time': 'Time6',
    'MyCustomField': 'MyCustomValidation',
    # Add your mappings here
}
```

### Custom Validation Patterns

```python
# Add custom validation patterns:
validation_patterns = {
    'custom_pattern': '^[A-Z]{2,4}$',
    'email_pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
}
```

## Troubleshooting

### Common Issues

#### 1. ImportError: No module named 'xmlschema'

```bash
# Solution: Install required packages
pip install xmlschema
```

#### 2. YAML Loading Error

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('your-file.yaml'))"
```

#### 3. Schema Validation Errors

```bash
# Validate JSON schema
python -c "import jsonschema; jsonschema.Draft7Validator.check_schema(json.load(open('schema.json')))"
```

#### 4. Permission Errors

```bash
# Make scripts executable
chmod +x *.py

# Or run with python explicitly
python script-name.py
```

### Debugging Tips

1. **Use verbose mode** for detailed output:
   ```bash
   python script-name.py --verbose
   ```

2. **Test with small files** before batch processing

3. **Check file paths** are correct and accessible

4. **Validate input files** before processing:
   ```bash
   # Validate YAML
   python -c "import yaml; yaml.safe_load(open('file.yaml'))"
   
   # Validate JSON
   python -c "import json; json.load(open('file.json'))"
   ```

## Best Practices

### 1. Version Control

- Keep original files in version control
- Use separate directories for enhanced files
- Tag releases after enhancement

### 2. Testing

- Test enhanced APIs with real data
- Validate against actual XML schema
- Check API documentation generation

### 3. Continuous Integration

- Automate schema conversion in CI/CD
- Validate enhanced APIs in pipeline
- Deploy enhanced APIs to staging first

### 4. Monitoring

- Monitor API validation errors
- Track enhancement success rates
- Log failed enhancements for review

## File Organization

```
schema-automation/
├── scripts/
│   ├── xsd-to-json-schema.py
│   ├── apply-schema-to-swagger.py
│   ├── batch-enhance-apis.py
│   └── requirements.txt
├── schemas/
│   ├── xml-schema.xsd
│   └── generated-json-schema.json
├── original-apis/
│   ├── api1.yaml
│   ├── api2.yaml
│   └── ...
├── enhanced-apis/
│   ├── enhanced-api1.yaml
│   ├── enhanced-api2.yaml
│   └── ...
└── docs/
    ├── automation-guide.md
    └── schema-mapping.md
```

## Performance Considerations

- **Large XML Schemas**: May take several minutes to convert
- **Batch Processing**: Process files in parallel for better performance
- **Memory Usage**: Large schema files may require more memory
- **Disk Space**: Enhanced files are typically 2-3x larger than originals

## Next Steps

1. **Test the automation** with your existing files
2. **Customize the scripts** for your specific requirements
3. **Integrate into CI/CD** pipeline
4. **Monitor and iterate** based on results
5. **Share with team** and train on usage

---

*For additional support or questions about the automation scripts, refer to the individual script help or the schema documentation.*