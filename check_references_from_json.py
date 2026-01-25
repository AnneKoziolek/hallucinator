#!/usr/bin/env python3
"""
Process references from a JSON file (from reference verification pipeline)
and check them for hallucinations using the existing hallucinator logic.

Usage:
    python check_references_from_json.py <json_file> [--no-color] [--sleep=SECONDS] [--openalex-key=KEY] [--output=FILE]
"""

import json
import sys
import os
import time
import contextlib
import urllib.parse
import requests

# Import the core functions from check_hallucinated_references
from check_hallucinated_references import (
    validate_authors,
    query_openalex,
    query_crossref,
    query_arxiv,
    query_dblp,
    print_hallucinated_reference,
    Colors,
    normalize_title,
    get_query_words,
)


def query_openalex_enhanced(title, api_key):
    """Query OpenAlex API for paper information with extended details.
    
    Returns: (found_title, found_authors, openalex_id, openalex_url, pub_year) tuple
    """
    words = get_query_words(title, 6)
    query = ' '.join(words)
    url = f"https://api.openalex.org/works?filter=title.search:{urllib.parse.quote(query)}&api_key={api_key}"
    try:
        response = requests.get(url, headers={"User-Agent": "Academic Reference Parser"})
        if response.status_code != 200:
            return None, [], None, None, None
        results = response.json().get("results", [])
        for item in results[:5]:  # Check top 5 results
            found_title = item.get("title", "")
            if found_title and normalize_title(title) in normalize_title(found_title) or \
               normalize_title(found_title) in normalize_title(title) or \
               len(normalize_title(title)) > 0 and \
               abs(len(normalize_title(title)) - len(normalize_title(found_title))) < 10:
                
                # Extract author names from authorships
                authorships = item.get("authorships", [])
                authors = []
                for authorship in authorships:
                    author_info = authorship.get("author", {})
                    display_name = author_info.get("display_name", "")
                    if display_name:
                        authors.append(display_name)
                
                openalex_id = item.get("id", "")  # Format: https://openalex.org/W1234567890
                openalex_url = openalex_id if openalex_id.startswith("http") else f"https://openalex.org/{openalex_id}" if openalex_id else None
                pub_year = item.get("publication_year", None)
                
                return found_title, authors, openalex_id, openalex_url, pub_year
    except Exception as e:
        print(f"[Error] OpenAlex search failed: {e}")
    return None, [], None, None, None


def load_references_from_json(json_file):
    """Load references from the JSON file format."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[Error] Failed to parse JSON file: {e}")
        return []
    
    # Handle both list and single object formats
    if isinstance(data, dict):
        data = [data]
    
    all_references = []
    
    for paper in data:
        pdf_name = paper.get('pdf', 'unknown')
        references = paper.get('references', [])
        
        for ref in references:
            title = ref.get('title') or ''
            if isinstance(title, str):
                title = title.strip()
            else:
                title = ''
            
            authors = ref.get('authors', []) or []
            year = ref.get('year') or ''
            doi = ref.get('doi', None)
            
            # Skip if no title or authors
            if not title or not authors:
                continue
            
            all_references.append({
                'title': title,
                'authors': authors,
                'year': year,
                'doi': doi,
                'pdf': pdf_name,
                'verification': ref.get('verification', {})
            })
    
    return all_references


def check_references_from_json(json_file, sleep_time=1.0, openalex_key=None, output_file=None):
    """Check references from JSON file against academic databases."""
    
    references = load_references_from_json(json_file)
    
    if not references:
        print("[Error] No valid references found in JSON file")
        return
    
    print(f"Processing {len(references)} references from {json_file}")
    print("="*60)
    print()
    
    # Open output file for streaming results if specified
    output_f = None
    if output_file:
        output_f = open(output_file, 'w', encoding='utf-8')
        output_f.write(f"Processing {len(references)} references from {json_file}\n")
        output_f.write("="*60 + "\n\n")
    
    # Prepare results list for JSON output
    results = []
    
    found = 0
    failed = 0
    mismatched = 0
    skipped = 0
    
    for i, ref in enumerate(references, 1):
        title = ref['title']
        ref_authors = ref['authors']
        year = ref['year']
        pdf = ref['pdf']
        
        status_line = f"[{i}/{len(references)}] {title}"
        print(status_line)
        if output_f:
            output_f.write(status_line + "\n")
        
        # Show authors
        authors_line = f"        Authors: {', '.join(ref_authors)}"
        print(authors_line)
        if output_f:
            output_f.write(authors_line + "\n")
        
        # Optional: Show year and PDF source
        if year:
            year_line = f"        Year: {year}"
            print(year_line)
            if output_f:
                output_f.write(year_line + "\n")
        
        pdf_line = f"        PDF: {pdf}"
        print(pdf_line)
        if output_f:
            output_f.write(pdf_line + "\n")
        
        # Query services in order
        found_title = None
        found_authors = None
        source = None
        openalex_url = None
        openalex_id = None
        pub_year = None
        
        # 1. OpenAlex (if API key provided)
        if openalex_key:
            print(f"        → Searching OpenAlex...")
            if output_f:
                output_f.write(f"        → Searching OpenAlex...\n")
            found_title, found_authors, openalex_id, openalex_url, pub_year = query_openalex_enhanced(title, openalex_key)
            if found_title and found_authors:
                source = "OpenAlex"
                # Continue to validation below
            else:
                found_title = None
                found_authors = None
                openalex_url = None
        
        # 2. CrossRef (if not found in OpenAlex)
        if not found_title:
            print(f"        → Searching CrossRef...")
            if output_f:
                output_f.write(f"        → Searching CrossRef...\n")
            found_title, found_authors = query_crossref(title)
            if found_title:
                source = "CrossRef"
        
        # 3. arXiv (if not found in CrossRef)
        if not found_title:
            print(f"        → Searching arXiv...")
            if output_f:
                output_f.write(f"        → Searching arXiv...\n")
            found_title, found_authors = query_arxiv(title)
            if found_title:
                source = "arXiv"
        
        # 4. DBLP - sleep before to avoid rate limiting
        if not found_title:
            print(f"        → Searching DBLP (waiting {sleep_time}s)...")
            if output_f:
                output_f.write(f"        → Searching DBLP (waiting {sleep_time}s)...\n")
            time.sleep(sleep_time)
            found_title, found_authors = query_dblp(title)
            if found_title:
                source = "DBLP"
        
        # Determine verification status
        verification_status = "not_found"
        if found_title:
            if validate_authors(ref_authors, found_authors):
                verification_status = "verified"
            else:
                verification_status = "author_mismatch"
        
        # Create result entry
        result_entry = {
            "title": title,
            "authors": ref_authors,
            "year": year,
            "doi": ref.get('doi'),
            "pdf": pdf,
            "original_verification": ref.get('verification', {}),
            "hallucinator_check": {
                "status": verification_status,
                "source": source,
                "found_title": found_title,
                "found_authors": found_authors,
                "publication_year": pub_year,
                "openalex_url": openalex_url
            }
        }
        results.append(result_entry)
        
        # Process results and display
        if found_title:
            if validate_authors(ref_authors, found_authors):
                result_line = f"        ✓ Found in {source}"
                print(result_line)
                if output_f:
                    output_f.write(result_line + "\n")
                
                # Show additional details for OpenAlex
                if source == "OpenAlex" and openalex_url:
                    detail_line = f"        Found title: {found_title}"
                    print(detail_line)
                    if output_f:
                        output_f.write(detail_line + "\n")
                    
                    found_authors_line = f"        Found authors: {', '.join(found_authors)}"
                    print(found_authors_line)
                    if output_f:
                        output_f.write(found_authors_line + "\n")
                    
                    if pub_year:
                        year_line = f"        Published: {pub_year}"
                        print(year_line)
                        if output_f:
                            output_f.write(year_line + "\n")
                    
                    url_line = f"        OpenAlex URL: {openalex_url}"
                    print(url_line)
                    if output_f:
                        output_f.write(url_line + "\n")
                
                found += 1
            else:
                result_line = f"        ✗ Author mismatch in {source}"
                print(result_line)
                if output_f:
                    output_f.write(result_line + "\n")
                
                # Show details for OpenAlex mismatches too
                if source == "OpenAlex" and openalex_url:
                    detail_line = f"        Found title: {found_title}"
                    print(detail_line)
                    if output_f:
                        output_f.write(detail_line + "\n")
                    
                    url_line = f"        OpenAlex URL: {openalex_url}"
                    print(url_line)
                    if output_f:
                        output_f.write(url_line + "\n")
                    
                    ref_authors_str = ", ".join(ref_authors)
                    found_authors_str = ", ".join(found_authors)
                    
                    authors_line = f"        Paper authors: {ref_authors_str}"
                    found_line = f"        Found authors: {found_authors_str}"
                    print(authors_line)
                    print(found_line)
                    if output_f:
                        output_f.write(authors_line + "\n")
                        output_f.write(found_line + "\n")
                
                print_hallucinated_reference(
                    title, "author_mismatch", source=source,
                    ref_authors=ref_authors, found_authors=found_authors
                )
                mismatched += 1
        else:
            result_line = f"        ✗ Not found in any database (potential hallucination)"
            print(result_line)
            if output_f:
                output_f.write(result_line + "\n")
            print_hallucinated_reference(title, "not_found", searched_openalex=bool(openalex_key))
            failed += 1
        
        print()
        if output_f:
            output_f.write("\n")
            output_f.flush()  # Flush to file immediately
    
    # Print summary
    print()
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"  Total references analyzed: {len(references)}")
    print(f"  {Colors.GREEN}Verified:{Colors.RESET} {found}")
    if mismatched > 0:
        print(f"  {Colors.YELLOW}Author mismatches:{Colors.RESET} {mismatched}")
    if failed > 0:
        print(f"  {Colors.RED}Not found (potential hallucinations):{Colors.RESET} {failed}")
    print()
    
    # Write summary to output file
    if output_f:
        output_f.write("\n")
        output_f.write("="*60 + "\n")
        output_f.write("SUMMARY\n")
        output_f.write("="*60 + "\n")
        output_f.write(f"  Total references analyzed: {len(references)}\n")
        output_f.write(f"  Verified: {found}\n")
        if mismatched > 0:
            output_f.write(f"  Author mismatches: {mismatched}\n")
        if failed > 0:
            output_f.write(f"  Not found (potential hallucinations): {failed}\n")
        output_f.write("\n")
        output_f.close()
    
    # Write results to JSON file
    json_output_file = "results.json"
    try:
        with open(json_output_file, 'w', encoding='utf-8') as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)
        print(f"Results written to {json_output_file}")
    except Exception as e:
        print(f"[Error] Failed to write results.json: {e}")


if __name__ == "__main__":
    # Check for --no-color flag
    if '--no-color' in sys.argv:
        Colors.disable()
        sys.argv.remove('--no-color')
    
    # Check for --output / -o flag
    output_path = None
    for i, arg in enumerate(sys.argv[:]):
        if arg.startswith('--output='):
            output_path = arg.split('=', 1)[1]
            sys.argv.remove(arg)
            break
        elif arg in ('--output', '-o') and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            sys.argv.remove(sys.argv[i + 1])
            sys.argv.remove(arg)
            break
    
    # Check for --sleep flag
    sleep_time = 1.0
    for i, arg in enumerate(sys.argv):
        if arg.startswith('--sleep='):
            sleep_time = float(arg.split('=')[1])
            sys.argv.remove(arg)
            break
        elif arg == '--sleep' and i + 1 < len(sys.argv):
            sleep_time = float(sys.argv[i + 1])
            sys.argv.remove(sys.argv[i + 1])
            sys.argv.remove(arg)
            break
    
    # Check for --openalex-key flag
    openalex_key = None
    for i, arg in enumerate(sys.argv[:]):
        if arg.startswith('--openalex-key='):
            openalex_key = arg.split('=', 1)[1]
            sys.argv.remove(arg)
            break
        elif arg == '--openalex-key' and i + 1 < len(sys.argv):
            openalex_key = sys.argv[i + 1]
            sys.argv.remove(sys.argv[i + 1])
            sys.argv.remove(arg)
            break
    
    if len(sys.argv) < 2:
        print("Usage: check_references_from_json.py [--no-color] [--sleep=SECONDS] [--openalex-key=KEY] [--output=FILE|-o FILE] <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found")
        sys.exit(1)
    
    if output_path:
        Colors.disable()
        with open(output_path, "w", encoding="utf-8") as f, \
             contextlib.redirect_stdout(f), \
             contextlib.redirect_stderr(f):
            check_references_from_json(json_file, sleep_time=sleep_time, openalex_key=openalex_key, output_file=None)
    else:
        check_references_from_json(json_file, sleep_time=sleep_time, openalex_key=openalex_key, output_file="results.txt")
