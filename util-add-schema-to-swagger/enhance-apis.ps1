#!/usr/bin/env pwsh
<#
.SYNOPSIS
    PowerShell wrapper for TFS API schema enhancement automation

.DESCRIPTION
    This script provides a convenient PowerShell interface for the Python-based
    schema automation tools. It handles the conversion of XML schemas to JSON
    and applies comprehensive validation to Swagger/OpenAPI files.

.PARAMETER XsdFile
    Path to the XML Schema (XSD) file to convert

.PARAMETER SwaggerFiles
    Path to Swagger YAML file(s) or directory containing multiple files

.PARAMETER OutputDir
    Directory where enhanced files will be saved

.PARAMETER Strict
    Enable strict validation mode (additionalProperties: false)

.PARAMETER Backup
    Create backup copies of original files

.PARAMETER Verbose
    Enable verbose output for detailed processing information

.PARAMETER DryRun
    Show what files would be processed without making changes

.EXAMPLE
    .\enhance-apis.ps1 -XsdFile "schema.xsd" -SwaggerFiles "api.yaml" -OutputDir "enhanced"
    
.EXAMPLE
    .\enhance-apis.ps1 -XsdFile "schema.xsd" -SwaggerFiles "apis\" -OutputDir "enhanced" -Strict -Verbose
    
.EXAMPLE
    .\enhance-apis.ps1 -XsdFile "schema.xsd" -SwaggerFiles "apis\" -OutputDir "enhanced" -DryRun
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="Path to XML Schema (XSD) file")]
    [string]$XsdFile,
    
    [Parameter(Mandatory=$true, HelpMessage="Path to Swagger file(s) or directory")]
    [string]$SwaggerFiles,
    
    [Parameter(Mandatory=$true, HelpMessage="Output directory for enhanced files")]
    [string]$OutputDir,
    
    [Parameter(HelpMessage="Enable strict validation mode")]
    [switch]$Strict,
    
    [Parameter(HelpMessage="Create backup copies of original files")]
    [switch]$Backup,
    
    [Parameter(HelpMessage="Enable verbose output")]
    [switch]$Verbose,
    
    [Parameter(HelpMessage="Show what would be processed without making changes")]
    [switch]$DryRun
)

# Script configuration
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$JsonSchemaFile = Join-Path $OutputDir "tfs-json-schema.json"

# Color output functions
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "ℹ️ $Message" -ForegroundColor Cyan }
function Write-Warning { param([string]$Message) Write-Host "⚠️ $Message" -ForegroundColor Yellow }

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python found: $pythonVersion"
        } else {
            throw "Python not found"
        }
    } catch {
        Write-Error "Python is required but not found. Please install Python 3.8+"
        exit 1
    }
    
    # Check required Python packages
    $requiredPackages = @('xmlschema', 'jsonschema', 'pyyaml')
    foreach ($package in $requiredPackages) {
        try {
            python -c "import $package" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Package found: $package"
            } else {
                throw "Package not found: $package"
            }
        } catch {
            Write-Warning "Installing missing package: $package"
            pip install $package
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install $package"
                exit 1
            }
        }
    }
    
    # Check script files exist
    $requiredScripts = @('xsd-to-json-schema.py', 'apply-schema-to-swagger.py', 'batch-enhance-apis.py')
    foreach ($script in $requiredScripts) {
        $scriptPath = Join-Path $ScriptDir $script
        if (-not (Test-Path $scriptPath)) {
            Write-Error "Required script not found: $scriptPath"
            exit 1
        }
    }
    
    Write-Success "All prerequisites satisfied"
}

# Validate input parameters
function Test-InputParameters {
    Write-Info "Validating input parameters..."
    
    # Check XSD file exists
    if (-not (Test-Path $XsdFile)) {
        Write-Error "XSD file not found: $XsdFile"
        exit 1
    }
    Write-Success "XSD file found: $XsdFile"
    
    # Check Swagger files/directory exists
    if (-not (Test-Path $SwaggerFiles)) {
        Write-Error "Swagger file(s) not found: $SwaggerFiles"
        exit 1
    }
    Write-Success "Swagger files found: $SwaggerFiles"
    
    # Create output directory if it doesn't exist
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
        Write-Success "Created output directory: $OutputDir"
    } else {
        Write-Success "Output directory exists: $OutputDir"
    }
}

# Convert XSD to JSON Schema
function Convert-XsdToJsonSchema {
    Write-Info "Converting XML Schema to JSON Schema..."
    
    $xsdScript = Join-Path $ScriptDir "xsd-to-json-schema.py"
    $args = @($XsdFile, $JsonSchemaFile)
    
    if ($Verbose) { $args += "--verbose" }
    
    try {
        python $xsdScript @args
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Schema conversion completed: $JsonSchemaFile"
        } else {
            throw "Schema conversion failed"
        }
    } catch {
        Write-Error "Failed to convert XSD to JSON Schema: $_"
        exit 1
    }
}

# Enhance Swagger files
function Invoke-SwaggerEnhancement {
    Write-Info "Enhancing Swagger files..."
    
    $isDirectory = (Get-Item $SwaggerFiles).PSIsContainer
    
    if ($isDirectory) {
        # Process directory with batch script
        $batchScript = Join-Path $ScriptDir "batch-enhance-apis.py"
        $args = @($SwaggerFiles, $JsonSchemaFile, $OutputDir)
        
        if ($Strict) { $args += "--strict" }
        if ($Verbose) { $args += "--verbose" }
        if ($DryRun) { $args += "--dry-run" }
        
        try {
            python $batchScript @args
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Batch enhancement completed"
            } else {
                throw "Batch enhancement failed"
            }
        } catch {
            Write-Error "Failed to enhance Swagger files: $_"
            exit 1
        }
    } else {
        # Process single file
        $enhanceScript = Join-Path $ScriptDir "apply-schema-to-swagger.py"
        $outputFile = Join-Path $OutputDir (Split-Path -Leaf $SwaggerFiles)
        $args = @($SwaggerFiles, $JsonSchemaFile, $outputFile)
        
        if ($Strict) { $args += "--strict" }
        if ($Verbose) { $args += "--verbose" }
        if ($Backup) { $args += "--backup" }
        
        if (-not $DryRun) {
            try {
                python $enhanceScript @args
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Enhancement completed: $outputFile"
                } else {
                    throw "Enhancement failed"
                }
            } catch {
                Write-Error "Failed to enhance Swagger file: $_"
                exit 1
            }
        } else {
            Write-Info "DRY RUN: Would enhance $SwaggerFiles -> $outputFile"
        }
    }
}

# Generate summary report
function Write-SummaryReport {
    Write-Host "`n📊 Enhancement Summary Report" -ForegroundColor Cyan
    Write-Host "==================================" -ForegroundColor Cyan
    
    Write-Host "Input Files:" -ForegroundColor Yellow
    Write-Host "  📄 XSD Schema: $XsdFile"
    Write-Host "  📁 Swagger Files: $SwaggerFiles"
    
    Write-Host "`nOutput:" -ForegroundColor Yellow  
    Write-Host "  📂 Output Directory: $OutputDir"
    Write-Host "  🔧 JSON Schema: $JsonSchemaFile"
    
    Write-Host "`nSettings:" -ForegroundColor Yellow
    Write-Host "  🔒 Strict Mode: $($Strict ? 'Enabled' : 'Disabled')"
    Write-Host "  💾 Backup: $($Backup ? 'Enabled' : 'Disabled')"
    Write-Host "  📝 Verbose: $($Verbose ? 'Enabled' : 'Disabled')"
    Write-Host "  👁️ Dry Run: $($DryRun ? 'Enabled' : 'Disabled')"
    
    if (Test-Path $OutputDir) {
        $outputFiles = Get-ChildItem $OutputDir -File
        Write-Host "`n📋 Generated Files ($($outputFiles.Count)):" -ForegroundColor Yellow
        foreach ($file in $outputFiles) {
            $size = [math]::Round($file.Length / 1KB, 2)
            Write-Host "  📄 $($file.Name) ($size KB)"
        }
    }
    
    Write-Host "`n✨ Enhancement process completed successfully!" -ForegroundColor Green
}

# Main execution
try {
    Write-Host "🚀 TFS API Schema Enhancement Tool" -ForegroundColor Magenta
    Write-Host "===================================" -ForegroundColor Magenta
    
    # Run prerequisite checks
    Test-Prerequisites
    
    # Validate parameters
    Test-InputParameters
    
    # Convert XSD to JSON Schema (skip if dry run)
    if (-not $DryRun) {
        Convert-XsdToJsonSchema
    } else {
        Write-Info "DRY RUN: Would convert $XsdFile to $JsonSchemaFile"
    }
    
    # Enhance Swagger files
    Invoke-SwaggerEnhancement
    
    # Generate summary
    Write-SummaryReport
    
} catch {
    Write-Error "Script execution failed: $_"
    exit 1
}

# Success exit
exit 0