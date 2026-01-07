#!/usr/bin/env python3
"""
Batch API Enhancement Script

This script processes multiple Swagger YAML files and applies schema validation to all of them.
Useful for enhancing entire API suites with consistent validation.

Usage:
    python batch-enhance-apis.py <input_dir> <schema_file> <output_dir> [options]

Requirements:
    pip install pyyaml jsonschema
"""

import argparse
import sys
from pathlib import Path
from typing import List
import subprocess


def find_swagger_files(directory: Path) -> List[Path]:
    """Find all Swagger YAML files in directory."""
    yaml_files = []
    patterns = ['*.yaml', '*.yml']
    
    for pattern in patterns:
        yaml_files.extend(directory.glob(pattern))
        yaml_files.extend(directory.rglob(pattern))
    
    # Filter for likely Swagger files
    swagger_files = []
    for file_path in yaml_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in ['openapi', 'swagger', 'paths', 'components']):
                    swagger_files.append(file_path)
        except Exception:
            continue
    
    return list(set(swagger_files))  # Remove duplicates


def enhance_api_file(swagger_file: Path, schema_file: Path, output_dir: Path, 
                    strict: bool = True) -> bool:
    """Enhance a single API file."""
    try:
        # Determine output path
        relative_path = swagger_file.name
        output_file = output_dir / relative_path
        
        # Run the enhancement script
        cmd = [
            sys.executable, 
            'apply-schema-to-swagger.py',
            str(swagger_file),
            str(schema_file), 
            str(output_file)
        ]
        
        if strict:
            cmd.append('--strict')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Enhanced: {swagger_file.name}")
            return True
        else:
            print(f"❌ Failed: {swagger_file.name} - {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Error enhancing {swagger_file.name}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Batch enhance multiple Swagger YAML files with schema validation'
    )
    
    parser.add_argument('input_dir', help='Directory containing Swagger YAML files')
    parser.add_argument('schema_file', help='Path to JSON schema file')
    parser.add_argument('output_dir', help='Directory for enhanced YAML files')
    parser.add_argument('--strict', action='store_true', help='Enable strict validation')
    parser.add_argument('--dry-run', action='store_true', help='Show files that would be processed')
    
    args = parser.parse_args()
    
    # Validate paths
    input_dir = Path(args.input_dir)
    schema_file = Path(args.schema_file)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        sys.exit(1)
    
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        sys.exit(1)
    
    # Find Swagger files
    swagger_files = find_swagger_files(input_dir)
    
    if not swagger_files:
        print(f"❌ No Swagger YAML files found in {input_dir}")
        sys.exit(1)
    
    print(f"📁 Found {len(swagger_files)} Swagger files in {input_dir}")
    
    if args.dry_run:
        print("\n🔍 Files that would be processed:")
        for file_path in swagger_files:
            print(f"   {file_path}")
        sys.exit(0)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process files
    successful = 0
    failed = 0
    
    print(f"\n🔄 Enhancing {len(swagger_files)} files...")
    
    for swagger_file in swagger_files:
        if enhance_api_file(swagger_file, schema_file, output_dir, args.strict):
            successful += 1
        else:
            failed += 1
    
    print(f"\n📊 Batch Enhancement Complete:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📂 Output directory: {output_dir}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()