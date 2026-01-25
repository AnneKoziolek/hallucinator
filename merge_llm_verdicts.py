#!/usr/bin/env python3
"""
Merge multiple LLM verification outputs and sort by verdict severity.

Usage:
    python3 merge_llm_verdicts.py <output.md> <file1.md> <file2.md> [file3.md ...]
    
Outputs:
    <output.md> - All references with both verdicts, sorted by severity
"""

import sys
import re
from collections import defaultdict


def parse_verdict_line(line):
    """
    Parse a line like:
    [ICSA_2026_paper_101_R1] DUBIOUS | "Title" — Authors (Year) | Explanation
    
    Returns: (ref_id, verdict, full_content) or None if not a verdict line
    """
    # Match pattern: [ref_id] VERDICT | rest
    match = re.match(r'\[([^\]]+)\]\s+(VERIFIED|DUBIOUS|CONFIRMED_HALLUCINATION)\s+\|\s+(.+)', line)
    if match:
        ref_id = match.group(1)
        verdict = match.group(2)
        rest = match.group(3)
        return (ref_id, verdict, line.strip())
    return None


def get_verdict_priority(verdicts):
    """
    Get sorting priority based on verdict(s).
    Lower number = higher priority (shown first).
    
    Priority:
    1. Two CONFIRMED_HALLUCINATION verdicts
    2. At least one CONFIRMED_HALLUCINATION
    3. Two DUBIOUS verdicts
    4. At least one DUBIOUS
    5. All VERIFIED
    """
    hallucination_count = verdicts.count('CONFIRMED_HALLUCINATION')
    dubious_count = verdicts.count('DUBIOUS')
    verified_count = verdicts.count('VERIFIED')
    
    if hallucination_count >= 2:
        return 1  # Two CONFIRMED_HALLUCINATION
    elif hallucination_count >= 1:
        return 2  # At least one CONFIRMED_HALLUCINATION
    elif dubious_count >= 2:
        return 3  # Two DUBIOUS
    elif dubious_count >= 1:
        return 4  # At least one DUBIOUS
    else:
        return 5  # All VERIFIED


def merge_verdicts(output_file, input_files):
    """
    Merge multiple verdict files and sort by severity.
    """
    # Dictionary: ref_id -> [(verdict, full_content), ...]
    verdicts_by_ref = defaultdict(list)
    
    # Parse each input file
    for file_num, input_file in enumerate(input_files, 1):
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[Error] Failed to read {input_file}: {e}")
            continue
        
        print(f"Processing file {file_num}: {input_file}")
        parsed_count = 0
        
        for line in lines:
            result = parse_verdict_line(line)
            if result:
                ref_id, verdict, full_content = result
                verdicts_by_ref[ref_id].append((verdict, full_content, file_num))
                parsed_count += 1
        
        print(f"  Parsed {parsed_count} verdicts")
    
    print()
    print(f"Total unique references: {len(verdicts_by_ref)}")
    print()
    
    # Sort references by verdict priority
    sorted_refs = []
    for ref_id, verdict_list in verdicts_by_ref.items():
        verdicts = [v[0] for v in verdict_list]
        priority = get_verdict_priority(verdicts)
        sorted_refs.append((priority, ref_id, verdict_list))
    
    sorted_refs.sort(key=lambda x: (x[0], x[1]))  # Sort by priority, then ref_id
    
    # Generate output
    lines = []
    
    lines.append("=" * 80)
    lines.append("MERGED LLM VERIFICATION RESULTS")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total references: {len(verdicts_by_ref)}")
    lines.append(f"Input files: {len(input_files)}")
    lines.append("")
    
    for i, file_path in enumerate(input_files, 1):
        lines.append(f"  File {i}: {file_path}")
    lines.append("")
    
    # Count by category
    priority_counts = defaultdict(int)
    for priority, _, _ in sorted_refs:
        priority_counts[priority] += 1
    
    lines.append("Summary by verdict:")
    if 1 in priority_counts:
        lines.append(f"  Two CONFIRMED_HALLUCINATION: {priority_counts[1]}")
    if 2 in priority_counts:
        lines.append(f"  At least one CONFIRMED_HALLUCINATION: {priority_counts[2]}")
    if 3 in priority_counts:
        lines.append(f"  Two DUBIOUS: {priority_counts[3]}")
    if 4 in priority_counts:
        lines.append(f"  At least one DUBIOUS: {priority_counts[4]}")
    if 5 in priority_counts:
        lines.append(f"  All VERIFIED: {priority_counts[5]}")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("")
    
    # Output sorted results
    current_priority = None
    for priority, ref_id, verdict_list in sorted_refs:
        # Add section header when priority changes
        if priority != current_priority:
            current_priority = priority
            lines.append("")
            lines.append("=" * 80)
            if priority == 1:
                header = "TWO CONFIRMED_HALLUCINATION VERDICTS"
            elif priority == 2:
                header = "AT LEAST ONE CONFIRMED_HALLUCINATION"
            elif priority == 3:
                header = "TWO DUBIOUS VERDICTS"
            elif priority == 4:
                header = "AT LEAST ONE DUBIOUS"
            else:
                header = "ALL VERIFIED"
            lines.append(header)
            lines.append("=" * 80)
            lines.append("")
        
        # Output all verdicts for this reference
        lines.append(f"[{ref_id}]")
        for verdict, full_content, file_num in verdict_list:
            # Extract just the verdict and explanation part (after the ref_id)
            content_match = re.match(r'\[[^\]]+\]\s+(.+)', full_content)
            if content_match:
                content = content_match.group(1)
                lines.append(f"  File {file_num}: {content}")
            else:
                lines.append(f"  File {file_num}: {full_content}")
        lines.append("")
    
    # Write output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"✓ Written: {output_file}")
        print(f"  ({len(verdicts_by_ref)} references with {len(input_files)} verdicts each)")
    except Exception as e:
        print(f"[Error] Failed to write {output_file}: {e}")
        return
    
    print()
    print("Results organized by severity:")
    print("  1. Two CONFIRMED_HALLUCINATION → Most confident hallucinations")
    print("  2. At least one CONFIRMED_HALLUCINATION → Likely hallucinations")
    print("  3. Two DUBIOUS → Uncertain citations")
    print("  4. At least one DUBIOUS → Some concerns")
    print("  5. All VERIFIED → References appear valid")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 merge_llm_verdicts.py <output.md> <file1.md> <file2.md> [file3.md ...]")
        print()
        print("Merges multiple LLM verification outputs and sorts by verdict severity.")
        print()
        print("Example:")
        print("  python3 merge_llm_verdicts.py merged-verdicts.md chatGPT-output1.md chatGPT-output2.md")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    # Verify all input files exist
    import os
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found")
            sys.exit(1)
    
    merge_verdicts(output_file, input_files)
