#!/usr/bin/env python3
"""
Convert filtered hallucination candidates to plain text format for LLM verification.

Outputs a text file with title, authors, and year for each suspected hallucination.
This can be fed to ChatGPT or similar LLM with web search to verify references.

Usage:
    python3 export_for_llm_verification.py <results-filtered-postprocessed.json>
"""

import json
import sys
import os


def export_for_llm(input_file):
    """
    Export filtered results to plain text format for LLM verification.
    
    Outputs: hallucination-candidates-for-verification.txt
    """
    
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
    
    print(f"Processing {len(results)} hallucination candidates...")
    print()
    
    # Organize by PDF
    by_pdf = {}
    for ref in results:
        pdf = ref.get('pdf', 'unknown')
        if pdf not in by_pdf:
            by_pdf[pdf] = []
        by_pdf[pdf].append(ref)
    
    # Generate text output
    lines = []
    
    lines.append("=" * 80)
    lines.append("SUSPECTED HALLUCINATED REFERENCES FOR VERIFICATION")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total suspected hallucinations: {len(results)}")
    lines.append("")
    lines.append("Instructions for LLM verification:")
    lines.append("  1. Use web search to verify each reference")
    lines.append("  2. Check if the title, authors, and year match")
    lines.append("  3. Mark as: VERIFIED, DUBIOUS, or CONFIRMED_HALLUCINATION")
    lines.append("  4. Note any findings about the actual paper vs the reference")
    lines.append("")
    lines.append("=" * 80)
    lines.append("")
    
    # Output by PDF for context
    for pdf in sorted(by_pdf.keys()):
        refs = by_pdf[pdf]
        paper_name = os.path.basename(pdf)
        lines.append(f"\nPAPER: {pdf}")
        lines.append(f"       ({len(refs)} suspected hallucinations)")
        lines.append("-" * 80)
        lines.append("")
        
        for i, ref in enumerate(refs, 1):
            title = ref.get('title', 'Unknown')
            authors = ref.get('authors', [])
            year = ref.get('year', 'Unknown Year')
            
            # Format authors
            if isinstance(authors, list):
                authors_str = ', '.join(authors) if authors else 'Unknown Authors'
            else:
                authors_str = str(authors)
            
            lines.append(f"[{i}] {title}")
            lines.append(f"    Authors: {authors_str}")
            lines.append(f"    Year: {year}")
            lines.append("")
    
    # Summary section for quick reference
    lines.append("")
    lines.append("=" * 80)
    lines.append("QUICK REFERENCE LIST FOR BATCH VERIFICATION")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Copy and paste the list below into an LLM with web search capability:")
    lines.append("")
    lines.append("-" * 80)
    
    for i, ref in enumerate(results, 1):
        title = ref.get('title', 'Unknown')
        authors = ref.get('authors', [])
        year = ref.get('year', '')
        
        if isinstance(authors, list):
            authors_str = ', '.join(authors) if authors else ''
        else:
            authors_str = str(authors)
        
        if year:
            line = f"{i}. \"{title}\" by {authors_str} ({year})"
        else:
            line = f"{i}. \"{title}\" by {authors_str}"
        
        lines.append(line)
    
    lines.append("-" * 80)
    lines.append("")
    
    # Prompt template for LLM
    lines.append("=" * 80)
    lines.append("PROMPT TEMPLATE FOR LLM VERIFICATION")
    lines.append("=" * 80)
    lines.append("")
    lines.append("""Please use web search to verify each of the following references. 
For each reference, determine if:
1. The paper exists and is correctly cited (VERIFIED)
2. The paper exists but has errors in title/authors/year (DUBIOUS - explain)
3. The paper cannot be found anywhere (CONFIRMED_HALLUCINATION)

Format your response as:
[1] Status | Explanation

References to verify:
""")
    lines.append("")
    
    for i, ref in enumerate(results, 1):
        title = ref.get('title', 'Unknown')
        authors = ref.get('authors', [])
        year = ref.get('year', '')
        
        if isinstance(authors, list):
            authors_str = ', '.join(authors) if authors else ''
        else:
            authors_str = str(authors)
        
        if year:
            line = f"[{i}] \"{title}\" - {authors_str} ({year})"
        else:
            line = f"[{i}] \"{title}\" - {authors_str}"
        
        lines.append(line)
    
    lines.append("")
    
    # Write output file
    output_file = 'hallucination-candidates-for-verification.txt'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"✓ Written: {output_file}")
    except Exception as e:
        print(f"[Error] Failed to write {output_file}: {e}")
        return
    
    print(f"  ({len(results)} hallucination candidates)")
    print()
    print("Next steps:")
    print(f"1. Open {output_file} in your text editor")
    print("2. Copy the 'PROMPT TEMPLATE FOR LLM VERIFICATION' section")
    print("3. Paste it into ChatGPT with web search enabled (GPT-4, Copilot, etc.)")
    print("4. Let the LLM verify the references")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 export_for_llm_verification.py <results-filtered-postprocessed.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    export_for_llm(input_file)
