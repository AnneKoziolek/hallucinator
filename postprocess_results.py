#!/usr/bin/env python3
"""
Post-process hallucinator results to classify references by type.

Classifies references into:
- standard_or_spec: Standards bodies (IEEE, ISO, AUTOSAR, W3C, etc.)
- industry_report: Consulting firms (McKinsey, Gartner, etc.)
- grey_spec: Grey literature (.org domains, specifications, white papers)
- scholarly_candidate: Likely scholarly publications (hallucination suspects if not_found)

Usage:
    python3 postprocess_results.py <results.json>
"""

import json
import sys
import os
import re


# Organization patterns for standards bodies
STANDARDS_ORGS = [
    'autosar', 'ieee', 'iso', 'w3c', 'ietf', 'itu', 'ansi', 'nist',
    'etsi', 'oasis', 'omg', 'ecma', 'iso/iec', 'iec', 'ogc', 'khronos',
    'unicode', 'whatwg', 'rfc', 'ieee computer society', 'acm standards'
]

# Industry consulting firms and analyst organizations
INDUSTRY_ORGS = [
    'mckinsey', 'gartner', 'forrester', 'bcg', 'accenture', 'deloitte',
    'pwc', 'kpmg', 'ey', 'idc', 'ovum', 'frost & sullivan', 'boston consulting',
    'bain', 'capgemini', 'cognizant', 'infosys'
]

# Grey literature keywords in title
GREY_KEYWORDS = [
    'specification', 'standard', 'white paper', 'technical report',
    'guide', 'guideline', 'manual', 'handbook', 'tutorial',
    'documentation', 'datasheet', 'data sheet', 'reference manual',
    'application note', 'technical note', 'best practices',
    'methodology', 'framework document', 'position paper'
]

# Domain patterns indicating non-scholarly sources
DOMAIN_PATTERNS = [
    r'www\.',
    r'\.org(?:\s|$|[/,])',
    r'\.com(?:\s|$|[/,])',
    r'\.net(?:\s|$|[/,])',
    r'\.gov(?:\s|$|[/,])',
    r'\.mil(?:\s|$|[/,])',
    r'\.edu(?:\s|$|[/,])',  # Sometimes grey lit
    r'https?://',
]

# Version/revision patterns
VERSION_PATTERNS = [
    r'\bR\d+\.\d+',  # R21.11
    r'\bv\d+\.\d+',  # v2.0
    r'\bversion\s+\d+',
    r'\brevision\s+\d+',
    r'\brel\.\s*\d+',
]


def classify_reference(ref):
    """
    Classify a reference by type based on heuristics.
    
    Returns: dict with 'type', 'reason', 'confidence'
    """
    title = ref.get('title', '').lower()
    authors = ref.get('authors', [])
    authors_str = ' '.join(authors).lower() if authors else ''
    
    # Check for standards organizations in authors
    for org in STANDARDS_ORGS:
        if org in authors_str:
            return {
                'type': 'standard_or_spec',
                'reason': f'Standards organization in authors: {org}',
                'confidence': 'high'
            }
    
    # Check for standards patterns in title
    if any(pattern in title for pattern in ['ieee', 'iso/', 'iec', 'rfc ']):
        return {
            'type': 'standard_or_spec',
            'reason': 'Standards pattern in title',
            'confidence': 'high'
        }
    
    # Check for industry consulting firms in authors
    for org in INDUSTRY_ORGS:
        if org in authors_str:
            return {
                'type': 'industry_report',
                'reason': f'Consulting/analyst firm in authors: {org}',
                'confidence': 'high'
            }
    
    # Check for domain patterns (URLs) in title or authors
    for pattern in DOMAIN_PATTERNS:
        if re.search(pattern, title) or re.search(pattern, authors_str):
            return {
                'type': 'grey_spec',
                'reason': 'URL/domain pattern detected',
                'confidence': 'high'
            }
    
    # Check for grey literature keywords in title
    for keyword in GREY_KEYWORDS:
        if keyword in title:
            return {
                'type': 'grey_spec',
                'reason': f'Grey literature keyword: {keyword}',
                'confidence': 'medium'
            }
    
    # Check for version/revision patterns indicating specifications
    for pattern in VERSION_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return {
                'type': 'grey_spec',
                'reason': 'Version/revision pattern (likely spec)',
                'confidence': 'medium'
            }
    
    # Check for single-word or organizational author names
    if authors and len(authors) == 1:
        author = authors[0].lower()
        # Single word authors that look like organizations
        words = author.split()
        if len(words) == 1 or any(w in author for w in ['association', 'institute', 'consortium', 'foundation', 'group']):
            return {
                'type': 'grey_spec',
                'reason': 'Organizational author name',
                'confidence': 'medium'
            }
    
    # Default: scholarly candidate
    return {
        'type': 'scholarly_candidate',
        'reason': 'No grey literature markers detected',
        'confidence': 'medium'
    }


def postprocess_results(input_file, output_dir=None):
    """
    Post-process results.json to add classifications.

    Args:
        input_file: path to results.json
        output_dir: directory for output files (default: current directory)

    Outputs:
    - results-postprocessed.json: All results with classifications
    - results-filtered-postprocessed.json: Only scholarly_candidate + not_found
    - report-postprocessed.txt: Statistics report
    """
    if output_dir is None:
        output_dir = '.'
    
    # Read input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except Exception as e:
        print(f"[Error] Failed to read {input_file}: {e}")
        return
    
    if not isinstance(results, list):
        print(f"[Error] Expected JSON array, got {type(results)}")
        return
    
    print(f"Processing {len(results)} references...")
    print()
    
    # Statistics
    stats = {
        'total': len(results),
        'by_type': {},
        'not_found_by_type': {},
        'author_mismatch_by_type': {},
        'verified_by_type': {}
    }
    
    # Process each reference
    postprocessed_results = []
    filtered_results = []
    
    for ref in results:
        # Classify the reference
        classification = classify_reference(ref)
        
        # Add classification to reference
        ref_with_classification = ref.copy()
        ref_with_classification['reference_classification'] = classification
        postprocessed_results.append(ref_with_classification)
        
        # Update statistics
        ref_type = classification['type']
        stats['by_type'][ref_type] = stats['by_type'].get(ref_type, 0) + 1
        
        # Get hallucinator status
        hallucinator_check = ref.get('hallucinator_check', {})
        status = hallucinator_check.get('status', 'unknown')
        
        if status == 'not_found':
            stats['not_found_by_type'][ref_type] = stats['not_found_by_type'].get(ref_type, 0) + 1
        elif status == 'author_mismatch':
            stats['author_mismatch_by_type'][ref_type] = stats['author_mismatch_by_type'].get(ref_type, 0) + 1
        elif status == 'verified':
            stats['verified_by_type'][ref_type] = stats['verified_by_type'].get(ref_type, 0) + 1
        
        # Filter: only scholarly_candidate + not_found
        if ref_type == 'scholarly_candidate' and status == 'not_found':
            filtered_results.append(ref_with_classification)
    
    # Write postprocessed results
    output_file = os.path.join(output_dir, 'results-postprocessed.json')
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(postprocessed_results, f, indent=2, ensure_ascii=False)
        print(f"✓ Written: {output_file}")
    except Exception as e:
        print(f"[Error] Failed to write {output_file}: {e}")
    
    # Write filtered results
    filtered_file = os.path.join(output_dir, 'results-filtered-postprocessed.json')
    try:
        with open(filtered_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, indent=2, ensure_ascii=False)
        print(f"✓ Written: {filtered_file}")
    except Exception as e:
        print(f"[Error] Failed to write {filtered_file}: {e}")
    
    # Generate report
    report = []
    report.append("=" * 70)
    report.append("REFERENCE CLASSIFICATION REPORT")
    report.append("=" * 70)
    report.append("")
    
    report.append(f"Total references processed: {stats['total']}")
    report.append("")
    
    # Overall classification breakdown
    report.append("Classification by Type:")
    report.append("-" * 50)
    for ref_type in sorted(stats['by_type'].keys()):
        count = stats['by_type'][ref_type]
        percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
        report.append(f"  {ref_type:30s}: {count:4d} ({percentage:5.1f}%)")
    report.append("")
    
    # Not found by type
    if stats['not_found_by_type']:
        report.append("NOT FOUND References by Type:")
        report.append("-" * 50)
        total_not_found = sum(stats['not_found_by_type'].values())
        for ref_type in sorted(stats['not_found_by_type'].keys()):
            count = stats['not_found_by_type'][ref_type]
            percentage = (count / total_not_found * 100) if total_not_found > 0 else 0
            report.append(f"  {ref_type:30s}: {count:4d} ({percentage:5.1f}%)")
        report.append(f"  {'TOTAL NOT FOUND':30s}: {total_not_found:4d}")
        report.append("")
    
    # Hallucination candidates
    hallucination_candidates = len(filtered_results)
    report.append("=" * 70)
    report.append("HALLUCINATION ANALYSIS")
    report.append("=" * 70)
    report.append("")
    report.append(f"True hallucination candidates: {hallucination_candidates}")
    report.append("  (scholarly_candidate + not_found status)")
    report.append("")
    
    if hallucination_candidates > 0:
        report.append("Suspected Hallucinations:")
        report.append("-" * 50)
        for i, ref in enumerate(filtered_results[:20], 1):  # Show first 20
            title = ref.get('title', 'Unknown')[:60]
            pdf = ref.get('pdf', 'unknown')
            report.append(f"{i:3d}. {title}")
            report.append(f"     PDF: {pdf}")
        
        if hallucination_candidates > 20:
            report.append(f"     ... and {hallucination_candidates - 20} more")
        report.append("")
    
    # Grey literature summary
    grey_count = stats['not_found_by_type'].get('standard_or_spec', 0) + \
                 stats['not_found_by_type'].get('industry_report', 0) + \
                 stats['not_found_by_type'].get('grey_spec', 0)
    
    if grey_count > 0:
        report.append("Grey Literature (not hallucinations):")
        report.append("-" * 50)
        report.append(f"  Standards/Specs     : {stats['not_found_by_type'].get('standard_or_spec', 0)}")
        report.append(f"  Industry Reports    : {stats['not_found_by_type'].get('industry_report', 0)}")
        report.append(f"  Other Grey Lit      : {stats['not_found_by_type'].get('grey_spec', 0)}")
        report.append(f"  Total Grey Literature: {grey_count}")
        report.append("")
    
    report.append("=" * 70)
    
    # Write report
    report_file = os.path.join(output_dir, 'report-postprocessed.txt')
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        print(f"✓ Written: {report_file}")
    except Exception as e:
        print(f"[Error] Failed to write {report_file}: {e}")
    
    # Print summary to console
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total references: {stats['total']}")
    print(f"  Standard/Spec: {stats['by_type'].get('standard_or_spec', 0)}")
    print(f"  Industry Report: {stats['by_type'].get('industry_report', 0)}")
    print(f"  Grey Spec: {stats['by_type'].get('grey_spec', 0)}")
    print(f"  Scholarly Candidate: {stats['by_type'].get('scholarly_candidate', 0)}")
    print()
    print(f"Not Found (total): {sum(stats['not_found_by_type'].values())}")
    print(f"  Standards/Grey Lit: {grey_count}")
    print(f"  TRUE HALLUCINATION CANDIDATES: {hallucination_candidates}")
    print()
    print(f"Output files:")
    print(f"  - {output_file} (all with classifications)")
    print(f"  - {filtered_file} (scholarly hallucinations only)")
    print(f"  - {report_file} (detailed report)")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 postprocess_results.py <results.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    postprocess_results(input_file)
