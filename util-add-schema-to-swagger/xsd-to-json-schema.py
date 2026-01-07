#!/usr/bin/env python3
"""
XSD to JSON Schema Converter

This script converts XML Schema (XSD) files to JSON Schema format,
specifically tailored for TFS trading API validation requirements.

Usage:
    python xsd-to-json-schema.py <input.xsd> <output.json>

Requirements:
    pip install xmlschema jsonschema pyyaml
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import xmlschema
except ImportError:
    print("Error: xmlschema library not found. Install with: pip install xmlschema")
    sys.exit(1)


class XSDToJSONSchemaConverter:
    """Converts XSD (XML Schema) to JSON Schema with TFS-specific optimizations."""
    
    def __init__(self):
        self.draft_version = "7"
        self.converted_types = {}
        self.enums = {}
        self.patterns = {}
        
    def convert_xsd_to_json_schema(self, xsd_file_path: str, output_path: str) -> Dict[str, Any]:
        """Main conversion method."""
        try:
            # Parse the XSD file
            print(f"📖 Parsing XSD file: {xsd_file_path}")
            schema = xmlschema.XMLSchema(xsd_file_path)
            print(f"✅ XSD parsed successfully - Found {len(schema.types)} types and {len(schema.elements)} elements")
            
            # Build JSON Schema structure
            json_schema = {
                "$schema": f"http://json-schema.org/draft-0{self.draft_version}/schema#",
                "$id": "https://fundserv.com/tfs/xml-aligned-schema",
                "title": "TFS Trading Schema - XML Aligned",
                "description": "JSON Schema automatically generated from TFS XML Schema for comprehensive validation",
                "type": "object",
                "additionalProperties": False,
                "definitions": {}
            }
            
            # Process all simple types
            print(f"🔧 Processing simple types...")
            self._process_simple_types(schema, json_schema)
            
            # Process complex types
            print(f"🔧 Processing complex types...")
            self._process_complex_types(schema, json_schema)
            
            # Process global elements
            print(f"🔧 Processing global elements...")
            self._process_global_elements(schema, json_schema)
            
            # Add root properties
            print(f"🔗 Setting up root properties...")
            if "OrdSet" in json_schema["definitions"]:
                json_schema["properties"] = {
                    "OrdSet": {"$ref": "#/definitions/OrdSet"}
                }
                print(f"   ✓ Added root property: OrdSet")
            
            # Write to output file
            print(f"💾 Writing JSON Schema to {output_path}...")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_schema, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Successfully converted {xsd_file_path} to {output_path}")
            print(f"📊 Generated {len(json_schema['definitions'])} schema definitions")
            
            return json_schema
            
        except Exception as e:
            print(f"❌ Error converting XSD to JSON Schema: {str(e)}")
            raise
    
    def _process_simple_types(self, schema: xmlschema.XMLSchema, json_schema: Dict[str, Any]):
        """Process XSD simple types and convert to JSON Schema definitions."""
        simple_count = 0
        for name, type_obj in schema.types.items():
            if hasattr(type_obj, 'is_simple') and type_obj.is_simple():
                json_type = self._convert_simple_type(type_obj, name)
                if json_type:
                    # Convert XSD naming to JSON Schema naming (e.g., string3-5 -> String3To5)
                    json_name = self._convert_type_name(name)
                    json_schema["definitions"][json_name] = json_type
                    simple_count += 1
                    print(f"   ✓ Simple type: {name} → {json_name}")
        print(f"📝 Processed {simple_count} simple types")
    
    def _process_complex_types(self, schema: xmlschema.XMLSchema, json_schema: Dict[str, Any]):
        """Process XSD complex types and convert to JSON Schema objects."""
        complex_count = 0
        for name, type_obj in schema.types.items():
            if hasattr(type_obj, 'is_complex') and type_obj.is_complex():
                json_type = self._convert_complex_type(type_obj, name)
                if json_type:
                    json_name = self._convert_type_name(name)
                    json_schema["definitions"][json_name] = json_type
                    complex_count += 1
                    prop_count = len(json_type.get('properties', {}))
                    print(f"   ✓ Complex type: {name} → {json_name} ({prop_count} properties)")
        print(f"📝 Processed {complex_count} complex types")
    
    def _process_global_elements(self, schema: xmlschema.XMLSchema, json_schema: Dict[str, Any]):
        """Process global elements from the XSD."""
        element_count = 0
        for name, element in schema.elements.items():
            if element.type:
                json_name = self._convert_type_name(name)
                if hasattr(element.type, 'is_simple') and element.type.is_simple():
                    json_type = self._convert_simple_type(element.type, name)
                    if json_type:
                        json_schema["definitions"][json_name] = json_type
                        element_count += 1
                        print(f"   ✓ Global element (simple): {name} → {json_name}")
                else:
                    # Reference to existing type
                    type_name = self._convert_type_name(element.type.name or name)
                    json_schema["definitions"][json_name] = {
                        "$ref": f"#/definitions/{type_name}"
                    }
                    element_count += 1
                    print(f"   ✓ Global element (ref): {name} → {json_name} → {type_name}")
        print(f"📝 Processed {element_count} global elements")
    
    def _convert_simple_type(self, type_obj, name: str) -> Optional[Dict[str, Any]]:
        """Convert XSD simple type to JSON Schema type."""
        json_type = {"type": "string"}
        
        # Debug logging
        print(f"      Processing type: {name} (type: {type(type_obj).__name__})")
        
        # Handle restrictions - check multiple ways to access facets
        facets_found = False
        
        # Method 1: Direct facets attribute
        if hasattr(type_obj, 'facets') and type_obj.facets:
            self._apply_facets(json_type, type_obj.facets, name)
            facets_found = True
            
        # Method 2: Via restrictions property
        if hasattr(type_obj, 'restrictions') and type_obj.restrictions:
            for restriction in type_obj.restrictions:
                if hasattr(restriction, 'facets') and restriction.facets:
                    self._apply_facets(json_type, restriction.facets, name)
                    facets_found = True
        
        # Method 3: Check if this is a restriction type
        if hasattr(type_obj, 'base_type') and hasattr(type_obj, 'constraints'):
            constraints = type_obj.constraints
            if constraints:
                for constraint_name, constraint_value in constraints.items():
                    if constraint_name == 'enumeration':
                        json_type['enum'] = list(constraint_value)
                        print(f"         Found enumeration: {constraint_value}")
                        facets_found = True
                    elif constraint_name == 'pattern':
                        pattern = self._convert_xsd_pattern_to_json(str(constraint_value))
                        json_type['pattern'] = pattern
                        print(f"         Found pattern: {constraint_value} → {pattern}")
                        facets_found = True
                    elif constraint_name == 'minLength':
                        json_type['minLength'] = int(constraint_value)
                        print(f"         Found minLength: {constraint_value}")
                        facets_found = True
                    elif constraint_name == 'maxLength':
                        json_type['maxLength'] = int(constraint_value)
                        print(f"         Found maxLength: {constraint_value}")
                        facets_found = True
                    elif constraint_name == 'length':
                        json_type['minLength'] = int(constraint_value)
                        json_type['maxLength'] = int(constraint_value)
                        print(f"         Found length: {constraint_value}")
                        facets_found = True
        
        # Method 4: Try iterating through validators/components
        if hasattr(type_obj, 'validators'):
            for validator in type_obj.validators:
                # Debug: check what validator attributes are available
                validator_type = type(validator).__name__
                print(f"         Validator type: {validator_type}")
                
                if hasattr(validator, 'enumeration') and validator.enumeration:
                    json_type['enum'] = list(validator.enumeration)
                    print(f"         Found enumeration via validator: {validator.enumeration}")
                    facets_found = True
                    
                # Handle specific facet types by name
                if validator_type == 'XsdPatternFacets':
                    if hasattr(validator, 'patterns'):
                        for pat in validator.patterns:
                            pattern = self._convert_xsd_pattern_to_json(str(pat))
                            json_type['pattern'] = pattern
                            print(f"         Found pattern facet: {pat} → {pattern}")
                            facets_found = True
                            break  # Take first pattern only
                    elif hasattr(validator, 'regexps'):
                        for pat in validator.regexps:
                            pattern = self._convert_xsd_pattern_to_json(str(pat))
                            json_type['pattern'] = pattern
                            print(f"         Found pattern regexp: {pat} → {pattern}")
                            facets_found = True
                            break  # Take first pattern only
                    elif hasattr(validator, 'value'):
                        pattern = self._convert_xsd_pattern_to_json(str(validator.value))
                        json_type['pattern'] = pattern
                        print(f"         Found pattern value: {validator.value} → {pattern}")
                        facets_found = True
                        
                elif validator_type == 'XsdMinLengthFacet' and hasattr(validator, 'value'):
                    json_type['minLength'] = int(validator.value)
                    print(f"         Found minLength facet: {validator.value}")
                    facets_found = True
                    
                elif validator_type == 'XsdMaxLengthFacet' and hasattr(validator, 'value'):
                    json_type['maxLength'] = int(validator.value)
                    print(f"         Found maxLength facet: {validator.value}")
                    facets_found = True
                    
                elif validator_type == 'XsdLengthFacet' and hasattr(validator, 'value'):
                    json_type['minLength'] = int(validator.value)
                    json_type['maxLength'] = int(validator.value)
                    print(f"         Found length facet: {validator.value}")
                    facets_found = True
        
        # Method 5: Try accessing patterns directly from the type object  
        if hasattr(type_obj, 'patterns') and type_obj.patterns:
            for pat in type_obj.patterns:
                # Extract pattern value from XML element
                pattern_value = None
                if hasattr(pat, 'value'):
                    pattern_value = pat.value
                elif hasattr(pat, 'get'):
                    pattern_value = pat.get('value')
                elif hasattr(pat, 'attrib') and 'value' in pat.attrib:
                    pattern_value = pat.attrib['value']
                elif str(pat).strip():
                    # Last resort: try to extract from string representation
                    import re
                    match = re.search(r'value=["\']([^"\']+)["\']', str(pat))
                    if match:
                        pattern_value = match.group(1)
                
                if pattern_value:
                    pattern = self._convert_xsd_pattern_to_json(str(pattern_value))
                    json_type['pattern'] = pattern
                    print(f"         Found direct pattern: {pattern_value} → {pattern}")
                    facets_found = True
                    break  # Take first pattern only
                else:
                    print(f"         Could not extract pattern value from: {pat}")
                    # Try to inspect the pattern object
                    if hasattr(pat, '__dict__'):
                        print(f"         Pattern attributes: {list(pat.__dict__.keys())}")
                    if hasattr(pat, 'tag'):
                        print(f"         Pattern tag: {pat.tag}")
                    if hasattr(pat, 'text'):
                        print(f"         Pattern text: {pat.text}")
                    if hasattr(pat, 'attrib'):
                        print(f"         Pattern attrib: {pat.attrib}")
        
        # Method 6: Check validators for XsdPatternFacet (singular)
        if hasattr(type_obj, 'validators'):
            for validator in type_obj.validators:
                validator_type = type(validator).__name__
                if validator_type == 'XsdPatternFacet':
                    if hasattr(validator, 'value'):
                        pattern = self._convert_xsd_pattern_to_json(str(validator.value))
                        json_type['pattern'] = pattern
                        print(f"         Found pattern facet value: {validator.value} → {pattern}")
                        facets_found = True
                    elif hasattr(validator, 'pattern'):
                        pattern = self._convert_xsd_pattern_to_json(str(validator.pattern))
                        json_type['pattern'] = pattern
                        print(f"         Found pattern facet pattern: {validator.pattern} → {pattern}")
                        facets_found = True
        
        # Handle base types for proper JSON Schema type
        if hasattr(type_obj, 'python_type'):
            if type_obj.python_type == int:
                json_type['type'] = 'integer'
            elif type_obj.python_type == float:
                json_type['type'] = 'number'
            elif type_obj.python_type == bool:
                json_type['type'] = 'boolean'
        elif hasattr(type_obj, 'base_type') and type_obj.base_type:
            # Check base type for numeric types
            base_name = getattr(type_obj.base_type, 'local_name', '')
            if base_name in ['int', 'integer', 'long', 'short']:
                json_type['type'] = 'integer'
            elif base_name in ['float', 'double', 'decimal']:
                json_type['type'] = 'number'
            elif base_name in ['boolean']:
                json_type['type'] = 'boolean'
        
        if not facets_found:
            print(f"         WARNING: No facets found for {name}")
            # Try to inspect the object
            attrs = [attr for attr in dir(type_obj) if not attr.startswith('_')]
            print(f"         Available attributes: {attrs[:10]}...")  # Show first 10
        
        # Note: Removed automatic description generation
        # Descriptions are optional in JSON Schema and were auto-generated
        
        return json_type
    
    def _apply_facets(self, json_type: Dict[str, Any], facets: Dict, name: str):
        """Apply XSD facets to JSON Schema type."""
        # Length constraints
        if 'minLength' in facets:
            json_type['minLength'] = int(facets['minLength'])
            print(f"         Found minLength: {facets['minLength']}")
        if 'maxLength' in facets:
            json_type['maxLength'] = int(facets['maxLength'])
            print(f"         Found maxLength: {facets['maxLength']}")
        if 'length' in facets:
            json_type['minLength'] = int(facets['length'])
            json_type['maxLength'] = int(facets['length'])
            print(f"         Found length: {facets['length']}")
        
        # Pattern constraints
        if 'pattern' in facets:
            pattern = self._convert_xsd_pattern_to_json(str(facets['pattern']))
            json_type['pattern'] = pattern
            print(f"         Found pattern: {facets['pattern']} → {pattern}")
        
        # Enumeration values
        if 'enumeration' in facets:
            json_type['enum'] = list(facets['enumeration'])
            print(f"         Found enumeration: {facets['enumeration']}")
    
    def _convert_complex_type(self, type_obj, name: str) -> Optional[Dict[str, Any]]:
        """Convert XSD complex type to JSON Schema object."""
        json_type = {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
            "description": f"Complex type: {name}"
        }
        
        required_fields = []
        
        # Process elements within the complex type
        if hasattr(type_obj, 'content') and hasattr(type_obj.content, 'iter_elements'):
            for element in type_obj.content.iter_elements():
                prop_name = element.local_name
                prop_type = self._get_property_type(element)
                
                json_type['properties'][prop_name] = prop_type
                
                # Check if required
                if hasattr(element, 'min_occurs') and element.min_occurs > 0:
                    required_fields.append(prop_name)
        
        # Process attributes
        if hasattr(type_obj, 'attributes'):
            for attr_name, attr in type_obj.attributes.items():
                prop_type = self._get_attribute_type(attr)
                json_type['properties'][attr_name] = prop_type
                
                if hasattr(attr, 'use') and attr.use == 'required':
                    required_fields.append(attr_name)
        
        if required_fields:
            json_type['required'] = required_fields
        
        return json_type
    
    def _get_property_type(self, element) -> Dict[str, Any]:
        """Get JSON Schema type for an element property."""
        if hasattr(element, 'type') and element.type:
            type_name = element.type.name
            if type_name:
                json_name = self._convert_type_name(type_name)
                return {"$ref": f"#/definitions/{json_name}"}
        
        # Default to string if type cannot be determined
        return {"type": "string"}
    
    def _get_attribute_type(self, attr) -> Dict[str, Any]:
        """Get JSON Schema type for an attribute."""
        if hasattr(attr, 'type') and attr.type:
            type_name = attr.type.name
            if type_name:
                json_name = self._convert_type_name(type_name)
                return {"$ref": f"#/definitions/{json_name}"}
        
        return {"type": "string"}
    
    def _convert_xsd_pattern_to_json(self, xsd_pattern: str) -> str:
        """Convert XSD regex pattern to JSON Schema compatible pattern."""
        # XSD uses \d, \w, etc. which are the same in JSON Schema
        # But we need to ensure proper anchoring
        pattern = xsd_pattern
        
        # Check if pattern contains alternation (|) that needs grouping
        if '|' in pattern and not (pattern.startswith('(') and pattern.endswith(')')):
            # Pattern has alternation but isn't grouped - wrap in parentheses
            pattern = f"({pattern})"
        
        # Add anchors if not present
        if not pattern.startswith('^'):
            pattern = '^' + pattern
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        
        # Do NOT manually escape backslashes - json.dumps() handles this automatically
        # The manual escaping was causing double-escaping bug
        
        return pattern
    
    def _convert_type_name(self, xsd_name: str) -> str:
        """Convert XSD type name to JSON Schema naming convention."""
        if not xsd_name:
            return "UnknownType"
        
        # Remove namespace prefixes
        if ':' in xsd_name:
            xsd_name = xsd_name.split(':')[-1]
        
        # Convert common patterns
        conversions = {
            'string2-20': 'String2To20',
            'string3-5': 'String3To5',
            'string5-7': 'String5To7',
            'string2-80': 'String2To80',
            'alpha3-4': 'Alpha3To4',
            'alphanum1-5': 'AlphaNum1To5',
            'amt9v2n': 'Amt9V2N',
            'percent2v3': 'Percent2V3',
            'percent3v2': 'Percent3V2',
            'value14': 'Value14',
            'date8': 'Date8',
            'time6': 'Time6',
            'integer3': 'Integer3',
            'integer5': 'Integer5',
            'length4': 'Length4',
            'sintype': 'SINType',
            'yes1': 'Yes1',
            'yesno1': 'YesNo1',
        }
        
        if xsd_name.lower() in conversions:
            return conversions[xsd_name.lower()]
        
        # Default: Convert to PascalCase
        words = re.split(r'[_\-\s]+', xsd_name)
        return ''.join(word.capitalize() for word in words if word)
    
    def _generate_description(self, name: str, json_type: Dict[str, Any]) -> str:
        """Generate a descriptive text for the schema type."""
        descriptions = {
            'date8': 'Date in YYYYMMDD format with validation',
            'time6': 'Time in HHMMSS format',
            'string3-5': 'String with length 3-5 characters',
            'string5-7': 'String with length 5-7 characters', 
            'amt9v2n': 'Amount with up to 9 digits before decimal and 2 after, optional negative',
            'value14': 'Decimal value with up to 9 digits before and 2-4 after decimal',
            'percent2v3': 'Percentage with up to 2 digits before and 3 after decimal',
            'mgmtcode': 'Management code - 2 letters followed by letter or digit',
            'alpha3-4': '3-4 uppercase letters',
            'alphanum1-5': '1-5 alphanumeric characters',
            'srctype': 'Source type - D for Dealer, I for Intermediary, F for Fund',
            'actncode': 'Action code for transaction operations',
            'yes1': 'Single Yes flag',
            'yesno1': 'Yes/No flag'
        }
        
        name_lower = name.lower()
        if name_lower in descriptions:
            return descriptions[name_lower]
        
        # Generate based on properties
        parts = []
        if 'minLength' in json_type and 'maxLength' in json_type:
            parts.append(f"String with length {json_type['minLength']}-{json_type['maxLength']} characters")
        elif 'maxLength' in json_type:
            parts.append(f"String with maximum {json_type['maxLength']} characters")
        
        if 'pattern' in json_type:
            parts.append("with pattern validation")
        
        if 'enum' in json_type:
            parts.append(f"Enumeration: {', '.join(json_type['enum'])}")
        
        return ' '.join(parts) if parts else f"Type: {name}"


def main():
    parser = argparse.ArgumentParser(
        description='Convert XML Schema (XSD) to JSON Schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python xsd-to-json-schema.py schema.xsd output.json
        """
    )
    
    parser.add_argument('input_xsd', help='Path to input XSD file')
    parser.add_argument('output_json', help='Path to output JSON Schema file')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input_xsd).exists():
        print(f"❌ Error: Input file '{args.input_xsd}' not found")
        sys.exit(1)
    
    # Create output directory if needed
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        converter = XSDToJSONSchemaConverter()
        
        print(f"🔄 Converting {args.input_xsd} to {args.output_json}...")
        print(f"📋 Using JSON Schema draft version: 7")
        
        result = converter.convert_xsd_to_json_schema(args.input_xsd, args.output_json)
        
        print(f"\n📈 Final Conversion Summary:")
        simple_types = [d for d in result['definitions'].values() if d.get('type') == 'string']
        complex_types = [d for d in result['definitions'].values() if d.get('type') == 'object']
        ref_types = [d for d in result['definitions'].values() if '$ref' in d]
        enum_types = [d for d in result['definitions'].values() if 'enum' in d]
        pattern_types = [d for d in result['definitions'].values() if 'pattern' in d]
        
        print(f"   Simple types: {len(simple_types)}")
        print(f"   Complex types: {len(complex_types)}")
        print(f"   Reference types: {len(ref_types)}")
        print(f"   Enumeration types: {len(enum_types)}")
        print(f"   Pattern-constrained types: {len(pattern_types)}")
        print(f"   Total definitions: {len(result['definitions'])}")
        print(f"   Root properties: {len(result.get('properties', {}))}")
        
    except Exception as e:
        print(f"❌ Conversion failed: {str(e)}")
        print(f"🔍 Error details:")
        print(f"   Input file: {args.input_xsd}")
        print(f"   Output file: {args.output_json}")
        print(f"   Current working directory: {Path.cwd()}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()