#!/usr/bin/env python3
"""
End-to-end pipeline: PDF directory -> reference extraction -> verification ->
postprocessing -> LLM export.

Usage:
    python3 run_pipeline.py [-d papers/] [--openalex-key=KEY] [--sleep=0.5] [--output-dir=output/]
"""

import argparse
import glob
import json
import os
import sys

from check_hallucinated_references import extract_references_with_titles_and_authors
from check_references_from_json import verify_references
from postprocess_results import postprocess_results
from export_for_llm_verification import export_for_llm


def pdf_refs_to_dicts(pdf_path, refs):
    """Convert (title, authors) tuples to the dict format used by verify_references."""
    return [
        {
            'title': title,
            'authors': authors,
            'year': '',
            'doi': None,
            'pdf': pdf_path,
            'verification': {}
        }
        for title, authors in refs
        if title and authors
    ]


def run_pipeline(pdf_dir, sleep_time=1.0, openalex_key=None, output_dir='.'):
    """Run the full hallucination detection pipeline on a directory of PDFs.

    Steps:
        1. Extract references from each PDF
        2. Verify against academic databases (OpenAlex, CrossRef, arXiv, DBLP)
        3. Classify references (scholarly vs grey literature)
        4. Export hallucination candidates for LLM verification
    """
    # 1. Find all PDFs
    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, '*.pdf')))
    if not pdf_files:
        print(f"[Error] No PDF files found in {pdf_dir}")
        return

    print(f"Found {len(pdf_files)} PDF(s) in {pdf_dir}")
    print()

    # 2. Extract references from each PDF
    all_references = []
    for pdf_path in pdf_files:
        print(f"Extracting references from {os.path.basename(pdf_path)}...")
        refs = extract_references_with_titles_and_authors(pdf_path)
        ref_dicts = pdf_refs_to_dicts(pdf_path, refs)
        print(f"  Found {len(ref_dicts)} references")
        all_references.extend(ref_dicts)

    if not all_references:
        print("[Error] No references extracted from any PDF")
        return

    print(f"\nTotal references to verify: {len(all_references)}")
    print()

    # 3. Verify against databases
    results = verify_references(all_references, sleep_time, openalex_key)

    # 4. Write results.json
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, 'results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {results_path}")

    # 5. Postprocess (classify scholarly vs grey literature)
    postprocess_results(results_path, output_dir=output_dir)

    # 6. Export for LLM verification
    filtered_path = os.path.join(output_dir, 'results-filtered-postprocessed.json')
    if os.path.exists(filtered_path):
        # Check if there are any candidates
        with open(filtered_path, 'r', encoding='utf-8') as f:
            filtered = json.load(f)
        if filtered:
            export_for_llm(filtered_path, output_dir=output_dir)
        else:
            print("\nNo hallucination candidates found — skipping LLM export.")
    else:
        print(f"\n[Warning] {filtered_path} not found — skipping LLM export.")

    print("\nPipeline complete.")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='End-to-end PDF hallucination detection pipeline'
    )
    parser.add_argument(
        '-d', '--pdf-dir', default='papers/',
        help='Directory containing PDF files (default: papers/)'
    )
    parser.add_argument(
        '--openalex-key', default=None,
        help='OpenAlex API key for enhanced metadata'
    )
    parser.add_argument(
        '--sleep', type=float, default=0.5,
        help='Sleep between DBLP queries in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--output-dir', default='output/',
        help='Output directory for results (default: output/)'
    )
    args = parser.parse_args()

    if not os.path.isdir(args.pdf_dir):
        print(f"[Error] Directory '{args.pdf_dir}' not found")
        sys.exit(1)

    run_pipeline(args.pdf_dir, args.sleep, args.openalex_key, args.output_dir)
