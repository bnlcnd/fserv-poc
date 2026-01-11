#!/usr/bin/env python3
"""
Swagger Schema Applier

This script applies XML/JSON schema validation to existing Swagger/OpenAPI YAML files,
enhancing them with comprehensive validation rules while preserving the original structure.

Usage:
    python apply-schema-to-swagger.py <swagger.yaml> <schema.json> <output.yaml> [options]

Requirements:
    pip install pyyaml jsonschema
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

try:
    import yaml
except ImportError:
    print("Error: PyYAML library not found. Install with: pip install pyyaml")
    sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema library not found. Install with: pip install jsonschema")
    sys.exit(1)


class SwaggerSchemaApplier:
    """Applies comprehensive schema validation to Swagger/OpenAPI files."""
    
    def __init__(self):
        self.schema_mappings = {}
        self.applied_enhancements = []
        self.validation_patterns = {}
        
    def apply_schema_to_swagger(self, swagger_file: str, schema_file: str, output_file: str, 
                               strict_mode: bool = True) -> Dict[str, Any]:
        """Main method to apply schema validation to Swagger file."""
        try:
            # Load files
            swagger_data = self._load_yaml_file(swagger_file)
            schema_data = self._load_json_file(schema_file)
            
            print(f"📖 Loaded Swagger file: {swagger_file}")
            print(f"📖 Loaded schema file: {schema_file}")
            print(f"🔧 Strict mode: {strict_mode}")
            
            # Extract schema definitions
            self._extract_schema_definitions(schema_data)
            
            # Enhance Swagger components
            self._enhance_swagger_components(swagger_data, strict_mode)
            
            # Apply field-level validations
            self._apply_field_validations(swagger_data)
            
            # Add API-specific transaction type validations
            self._add_transaction_type_validations(swagger_data)
            
            # Enhance error handling schemas
            self._enhance_error_schemas(swagger_data)
            
            # Add comprehensive documentation
            self._add_schema_documentation(swagger_data)
            
            # Write enhanced Swagger file
            self._save_yaml_file(swagger_data, output_file)
            
            print(f"\n📊 Enhancement Summary:")
            for enhancement in self.applied_enhancements:
                print(f"   ✅ {enhancement}")
            
            print(f"✅ Successfully enhanced {swagger_file} -> {output_file}")
            return swagger_data
            
        except Exception as e:
            print(f"❌ Error applying schema to Swagger: {str(e)}")
            raise
    
    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Load YAML file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load YAML file {file_path}: {str(e)}")
    
    def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """Load JSON file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load JSON file {file_path}: {str(e)}")
    
    def _save_yaml_file(self, data: Dict[str, Any], file_path: str):
        """Save YAML file with proper formatting."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, 
                         allow_unicode=True, width=120, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save YAML file {file_path}: {str(e)}")
    
    def _extract_schema_definitions(self, schema_data: Dict[str, Any]):
        """Extract schema definitions for mapping."""
        if 'definitions' in schema_data:
            for name, definition in schema_data['definitions'].items():
                self.schema_mappings[name] = definition
                
                # Extract patterns for quick lookup
                if 'pattern' in definition:
                    self.validation_patterns[name] = definition['pattern']
        
        print(f"📋 Extracted {len(self.schema_mappings)} schema definitions")
    
    def _enhance_swagger_components(self, swagger_data: Dict[str, Any], strict_mode: bool):
        """Enhance Swagger components with schema validation."""
        if 'components' not in swagger_data:
            swagger_data['components'] = {}
        if 'schemas' not in swagger_data['components']:
            swagger_data['components']['schemas'] = {}
        
        schemas = swagger_data['components']['schemas']
        
        # Add base validation types from schema
        self._add_base_validation_types(schemas)
        
        # Enhance existing schemas
        self._enhance_existing_schemas(schemas, strict_mode)
        
        self.applied_enhancements.append("Enhanced component schemas with validation")
    
    def _add_base_validation_types(self, schemas: Dict[str, Any]):
        """Add fundamental validation types from schema."""
        # Get all schema types referenced in field mappings
        field_mappings = {
            'Date': 'Date8',
            'Time': 'Time6', 
            'MgmtCode': 'MgmtCodeType',
            'DlrCode': 'Length4',
            'IntCode': 'Alpha3To4',
            'SrcID': 'String15',
            'FundAcctID': 'String15',
            'FundID': 'String3To5',
            'OrdID': 'String5To7',
            'AmtValue': 'Value14',
            'SrcType': 'SrcType',  # This maps to base SrcType with enum
            'ActnCode': 'ActnCode',
            'AcctDesig': 'AcctDesigType',
            'AmtType': 'AmtType'
        }
        
        # Add commonly used base types
        additional_types = [
            'Amt9V2N', 'Percent2V3', 'AlphaNum1To5', 'Yes1', 'YesNo1', 
            'Integer3', 'Integer5'
        ]
        
        # Combine all required schema types
        all_schema_types = set(field_mappings.values()) | set(additional_types)
        
        added_count = 0
        for type_name in all_schema_types:
            if type_name in self.schema_mappings:
                schemas[type_name] = self.schema_mappings[type_name].copy()
                added_count += 1
                print(f"   ➕ Added base type: {type_name}")
        
        # Add specific enums
        self._add_enum_types(schemas)
        
        print(f"📦 Added {added_count} base validation types")
        self.applied_enhancements.append(f"Added {added_count} base validation types")
    
    def _add_enum_types(self, schemas: Dict[str, Any]):
        """Add enumeration types for API validation."""
        enums = {
            'SrcType': {
                'type': 'string',
                'enum': ['D', 'I', 'F'],
                'description': 'Source type - D for Dealer, I for Intermediary, F for Fund'
            },
            'ActnCode': {
                'type': 'string',
                'enum': ['NEW', 'CHG', 'CAN', 'CAX', 'AOT', 'REV'],
                'description': 'Action code'
            },
            'AcctDesigType': {
                'type': 'string',
                'enum': ['1', '2', '3'],
                'description': 'Account designation'
            },
            'AmtType': {
                'type': 'string',
                'enum': ['A', 'D', 'F', 'M', 'P', 'S', 'T', 'B', 'C', 'J', 'L', 'G', 'H'],
                'description': 'Amount type'
            },
            'SettlMethd': {
                'type': 'string',
                'enum': ['1', '2', '3', '4', '5', '6'],
                'description': 'Settlement method'
            },
            'RspnSrc': {
                'type': 'string',
                'enum': ['I', 'F', 'N'],
                'description': 'Response source'
            },
            'RtnCode': {
                'type': 'string',
                'enum': ['00', '01', '98', '99', '50'],
                'description': 'Return code'
            }
        }
        
        enum_count = 0
        for name, definition in enums.items():
            schemas[name] = definition
            enum_count += 1
            print(f"   ➕ Added enum: {name} with {len(definition.get('enum', []))} values")
        
        print(f"📋 Added {enum_count} enumeration types")
    
    def _enhance_existing_schemas(self, schemas: Dict[str, Any], strict_mode: bool):
        """Enhance existing schemas with validation rules."""
        enhanced_count = 0
        
        for name, schema in schemas.items():
            if isinstance(schema, dict):
                original_schema = schema.copy()
                
                # First enhance the schema object (for object types)
                self._enhance_schema_object(schema, strict_mode)
                
                # Then enhance top-level schemas that match our field mappings
                self._enhance_top_level_schema(name, schema)
                
                if schema != original_schema:
                    enhanced_count += 1
                    print(f"   🔧 Enhanced schema: {name}")
        
        if enhanced_count > 0:
            print(f"🔄 Enhanced {enhanced_count} existing schemas")
            self.applied_enhancements.append(f"Enhanced {enhanced_count} existing schemas")
    
    def _enhance_schema_object(self, schema: Dict[str, Any], strict_mode: bool):
        """Enhance a single schema object with validation."""
        if schema.get('type') == 'object':
            # Add additionalProperties: false for strict validation
            if strict_mode and 'additionalProperties' not in schema:
                schema['additionalProperties'] = False
            
            # Enhance properties
            if 'properties' in schema:
                for prop_name, prop_def in schema['properties'].items():
                    self._enhance_property(prop_name, prop_def)
    
    def _enhance_property(self, prop_name: str, prop_def: Dict[str, Any]):
        """Enhance a single property with appropriate validation."""
        # Apply field-specific validations based on name patterns
        field_mappings = {
            'Date': 'Date8',
            'Time': 'Time6', 
            'MgmtCode': 'MgmtCodeType',
            'DlrCode': 'Length4',
            'IntCode': 'Alpha3To4',
            'SrcID': 'String15',
            'FundAcctID': 'String15',
            'FundID': 'String3To5',
            'OrdID': 'String5To7',
            'AmtValue': 'Value14',
            'SrcType': 'SrcType',
            'ActnCode': 'ActnCode',
            'AcctDesig': 'AcctDesigType',
            'AmtType': 'AmtType'
        }
        
        # Check if property should inherit validation from a schema type
        for field_pattern, schema_type in field_mappings.items():
            schema_key = self._find_schema_key_case_insensitive(schema_type)
            if field_pattern in prop_name and schema_key:
                # Copy validation properties while preserving original metadata
                source_schema = self.schema_mappings[schema_key]
                
                # Preserve existing metadata
                original_docs = prop_def.get('externalDocs')
                original_example = prop_def.get('example')
                original_description = prop_def.get('description')
                
                # Copy validation properties from source schema
                if 'type' in source_schema:
                    prop_def['type'] = source_schema['type']
                if 'pattern' in source_schema:
                    prop_def['pattern'] = source_schema['pattern']
                if 'minLength' in source_schema:
                    prop_def['minLength'] = source_schema['minLength']
                if 'maxLength' in source_schema:
                    prop_def['maxLength'] = source_schema['maxLength']
                if 'enum' in source_schema:
                    prop_def['enum'] = source_schema['enum']
                if 'format' in source_schema:
                    prop_def['format'] = source_schema['format']
                
                # Restore original metadata
                if original_docs:
                    prop_def['externalDocs'] = original_docs
                if original_example:
                    prop_def['example'] = original_example
                if original_description:
                    prop_def['description'] = original_description
                
                print(f"   ✨ Enhanced {prop_name} with {schema_type} validation (preserving docs)")
                break
    
    def _enhance_top_level_schema(self, schema_name: str, schema_def: Dict[str, Any]):
        """Enhance top-level schema definitions with validation from JSON schema."""
        # Skip if this schema already has validation or isn't a string type
        if schema_def.get('type') != 'string':
            return
            
        # Map field names to their validation types
        field_mappings = {
            'Date': 'Date8', 'Time': 'Time6', 'MgmtCode': 'MgmtCodeType',
            'DlrCode': 'Length4', 'IntCode': 'Alpha3To4', 'SrcID': 'String15',
            'FundAcctID': 'String15', 'FundID': 'String3To5', 'OrdID': 'String5To7',
            'AmtValue': 'Value14', 'SrcType': 'SrcType', 'ActnCode': 'ActnCode',
            'AcctDesig': 'AcctDesigType', 'AmtType': 'AmtType'
        }
        
        # Check if this field should be enhanced with a specific validation type
        if schema_name in field_mappings:
            validation_type = field_mappings[schema_name]
            schema_key = self._find_schema_key_case_insensitive(validation_type)
            if schema_key:
                source_schema = self.schema_mappings[schema_key]
                
                # Preserve existing metadata
                original_docs = schema_def.get('externalDocs')
                original_example = schema_def.get('example')
                original_description = schema_def.get('description')
                
                # Copy validation properties from source schema
                if 'pattern' in source_schema:
                    schema_def['pattern'] = source_schema['pattern']
                if 'minLength' in source_schema:
                    schema_def['minLength'] = source_schema['minLength']
                if 'maxLength' in source_schema:
                    schema_def['maxLength'] = source_schema['maxLength']
                if 'enum' in source_schema:
                    schema_def['enum'] = source_schema['enum']
                if 'format' in source_schema:
                    schema_def['format'] = source_schema['format']
                    
                # Restore original metadata
                if original_docs:
                    schema_def['externalDocs'] = original_docs
                if original_example:
                    schema_def['example'] = original_example
                if original_description:
                    schema_def['description'] = original_description
                    
                print(f"   ✨ Enhanced top-level {schema_name} with {validation_type} validation (preserving docs)")
                return
        
        # Otherwise, check if we have direct validation for this schema name in our JSON schema
        schema_key = self._find_schema_key_case_insensitive(schema_name)
        if schema_key:
            print(f"   🔍 Found case-insensitive match for {schema_name} -> {schema_key}")
            json_validation = self.schema_mappings[schema_key]
            
            # Apply enum validation if present
            if 'enum' in json_validation:
                schema_def['enum'] = json_validation['enum']
                print(f"   📋 Added enum to {schema_name}: {json_validation['enum']}")
            
            # Apply pattern validation if present
            if 'pattern' in json_validation:
                schema_def['pattern'] = json_validation['pattern']
                print(f"   🔍 Added pattern to {schema_name}: {json_validation['pattern']}")
                
            # Apply length constraints if present
            if 'minLength' in json_validation:
                schema_def['minLength'] = json_validation['minLength']
                print(f"   📏 Added minLength to {schema_name}: {json_validation['minLength']}")
            if 'maxLength' in json_validation:
                schema_def['maxLength'] = json_validation['maxLength']
                print(f"   📏 Added maxLength to {schema_name}: {json_validation['maxLength']}")
                
            # Update description if JSON schema has one
            if 'description' in json_validation and 'description' not in schema_def:
                schema_def['description'] = json_validation['description']
        
    def _find_schema_key_case_insensitive(self, schema_name: str) -> Optional[str]:
        """Find schema key with case-insensitive matching."""
        # First try exact match
        if schema_name in self.schema_mappings:
            return schema_name
        
        # Then try case-insensitive match
        schema_name_lower = schema_name.lower()
        for key in self.schema_mappings.keys():
            if key.lower() == schema_name_lower:
                return key
        
        return None
        
        # Otherwise, check if we have direct validation for this schema name in our JSON schema
        schema_key = self._find_schema_key_case_insensitive(schema_name)
        if schema_name == 'SupConfirm':
            print(f"   🐛 DEBUG: SupConfirm case-insensitive lookup result: {schema_key}")
        if schema_key:
            print(f"   🔍 Found case-insensitive match for {schema_name} -> {schema_key}")
            json_validation = self.schema_mappings[schema_key]
            
            # Apply enum validation if present
            if 'enum' in json_validation:
                schema_def['enum'] = json_validation['enum']
                print(f"   📋 Added enum to {schema_name}: {json_validation['enum']}")
            
            # Apply pattern validation if present
            if 'pattern' in json_validation:
                schema_def['pattern'] = json_validation['pattern']
                print(f"   🔍 Added pattern to {schema_name}: {json_validation['pattern']}")
                
            # Apply length constraints if present
            if 'minLength' in json_validation:
                schema_def['minLength'] = json_validation['minLength']
                print(f"   📏 Added minLength to {schema_name}: {json_validation['minLength']}")
            if 'maxLength' in json_validation:
                schema_def['maxLength'] = json_validation['maxLength']
                print(f"   📏 Added maxLength to {schema_name}: {json_validation['maxLength']}")
                
            # Update description if JSON schema has one
            if 'description' in json_validation and 'description' not in schema_def:
                schema_def['description'] = json_validation['description']
    
    def _apply_field_validations(self, swagger_data: Dict[str, Any]):
        """Apply field-level validations throughout the Swagger file."""
        if 'components' in swagger_data and 'schemas' in swagger_data['components']:
            self._apply_validations_to_schemas(swagger_data['components']['schemas'])
        
        self.applied_enhancements.append("Applied field-level validations")
    
    def _apply_validations_to_schemas(self, schemas: Dict[str, Any]):
        """Recursively apply validations to all schemas."""
        for schema_name, schema_def in schemas.items():
            if isinstance(schema_def, dict):
                self._apply_validation_to_schema(schema_def)
    
    def _apply_validation_to_schema(self, schema_def: Dict[str, Any]):
        """Apply validation to a single schema definition."""
        if schema_def.get('type') == 'string':
            # Apply string validations
            self._apply_string_validations(schema_def)
        elif schema_def.get('type') == 'object':
            # Recursively apply to properties
            if 'properties' in schema_def:
                for prop_def in schema_def['properties'].values():
                    if isinstance(prop_def, dict):
                        self._apply_validation_to_schema(prop_def)
    
    def _apply_string_validations(self, schema_def: Dict[str, Any]):
        """Apply appropriate string validations."""
        # Only apply patterns that are explicitly defined in the source schema
        # Do not add automatic patterns - follow the XML/JSON schema definitions exactly
        pass
    
    def _add_transaction_type_validations(self, swagger_data: Dict[str, Any]):
        """Add API-specific transaction type validations."""
        api_title = swagger_data.get('info', {}).get('title', '')
        
        # Determine API type and add appropriate transaction type enum
        transaction_types = {
            'Buy': {'enum': ['1'], 'description': 'Transaction type for Buy orders'},
            'Sell': {'enum': ['5'], 'description': 'Transaction type for Sell orders'},
            'Switch': {'enum': ['8'], 'description': 'Transaction type for Switch orders'},
            'Transfer': {'enum': ['7'], 'description': 'Transaction type for Transfer orders'},
            'ICT': {'enum': ['6'], 'description': 'Transaction type for ICT orders'}
        }
        
        if 'components' in swagger_data and 'schemas' in swagger_data['components']:
            for api_type, trxn_def in transaction_types.items():
                if api_type.lower() in api_title.lower():
                    trxn_type_name = f'TrxnTyp{api_type}'
                    swagger_data['components']['schemas'][trxn_type_name] = {
                        'type': 'string',
                        **trxn_def
                    }
                    break
        
        self.applied_enhancements.append("Added API-specific transaction type validation")
    
    def _enhance_error_schemas(self, swagger_data: Dict[str, Any]):
        """Enhance error handling schemas."""
        if 'components' not in swagger_data or 'schemas' not in swagger_data['components']:
            return
        
        schemas = swagger_data['components']['schemas']
        
        # Enhanced error schemas
        error_schemas = {
            'ErrorCode': {
                'type': 'string',
                'pattern': '^\\d{3}$',
                'description': '3-digit error code'
            },
            'CorrlatnID': {
                'type': 'string',
                'maxLength': 48,
                'description': 'Correlation ID for tracking'
            }
        }
        
        for name, definition in error_schemas.items():
            if name not in schemas:
                schemas[name] = definition
        
        self.applied_enhancements.append("Enhanced error handling schemas")
    
    def _add_schema_documentation(self, swagger_data: Dict[str, Any]):
        """Add comprehensive documentation to the enhanced schema."""
        # Add info about the enhancement
        if 'info' not in swagger_data:
            swagger_data['info'] = {}
        
        original_description = swagger_data['info'].get('description', '')
        enhancement_note = "\n\nThis API specification has been enhanced with comprehensive XML schema-based validation."
        
        if enhancement_note not in original_description:
            swagger_data['info']['description'] = original_description + enhancement_note
        
        # Add schema version info
        if 'x-schema-version' not in swagger_data['info']:
            swagger_data['info']['x-schema-version'] = 'XML-aligned-v1.0'
        
        self.applied_enhancements.append("Added comprehensive documentation")


def main():
    parser = argparse.ArgumentParser(
        description='Apply XML/JSON schema validation to Swagger/OpenAPI files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python apply-schema-to-swagger.py api.yaml schema.json enhanced-api.yaml
  python apply-schema-to-swagger.py api.yaml schema.json enhanced-api.yaml --strict
        """
    )
    
    parser.add_argument('swagger_file', help='Path to input Swagger/OpenAPI YAML file')
    parser.add_argument('schema_file', help='Path to JSON schema file')
    parser.add_argument('output_file', help='Path to output enhanced YAML file')
    parser.add_argument('--strict', action='store_true', 
                       help='Enable strict validation (additionalProperties: false)')
    
    args = parser.parse_args()
    
    # Validate input files exist
    for file_path in [args.swagger_file, args.schema_file]:
        if not Path(file_path).exists():
            print(f"❌ Error: File '{file_path}' not found")
            sys.exit(1)
    
    # Create output directory if needed
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        applier = SwaggerSchemaApplier()
        
        print(f"🔄 Enhancing {args.swagger_file} with schema from {args.schema_file}...")
        
        result = applier.apply_schema_to_swagger(
            args.swagger_file, 
            args.schema_file, 
            args.output_file, 
            strict_mode=args.strict
        )
        
        schemas_count = len(result.get('components', {}).get('schemas', {}))
        print(f"\n📈 Enhancement Complete:")
        print(f"   Total schemas: {schemas_count}")
        print(f"   Output file: {args.output_file}")
        
    except Exception as e:
        print(f"❌ Enhancement failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main() 