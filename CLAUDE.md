# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Python pipeline that detects hallucinated references in academic papers by verifying them against OpenAlex, CrossRef, arXiv, and DBLP, then classifying results and preparing them for LLM-based verification.

## Build & Run

```bash
source ../venv/bin/activate
pip install -r requirements.txt

# End-to-end: PDF directory -> extraction -> verification -> classification -> LLM export
python3 run_pipeline.py -d papers/ --sleep=0.5 --output-dir=output/

# Or run individual steps manually:
# Verify references (JSON input from external extraction tool)
python3 check_references_from_json.py --openalex-key=KEY --sleep=0.5 filtered.json

# Verify references directly from PDF (text output only, no JSON)
python3 check_hallucinated_references.py paper.pdf

# Classify scholarly vs grey literature
python3 postprocess_results.py results.json

# Export for LLM verification
python3 export_for_llm_verification.py results-filtered-postprocessed.json

# Merge multiple LLM verification runs
python3 merge_llm_verdicts.py merged-verdicts.md run1.md run2.md

# Run tests
python -m pytest tests/ -v
```

The venv lives at `../venv` (one level above this directory).

## Architecture

### Core verification (`check_hallucinated_references.py`)

Contains all shared logic: PDF extraction (PyMuPDF), reference parsing (IEEE/ACM/USENIX formats), database query functions (`query_openalex`, `query_crossref`, `query_arxiv`, `query_dblp`), fuzzy author matching (`validate_authors` using rapidfuzz), and title normalization. This is the module that other scripts import from.

### JSON wrapper (`check_references_from_json.py`)

Imports core functions from `check_hallucinated_references.py` and adds `query_openalex_enhanced()` which returns additional metadata (OpenAlex ID, URL, publication year). Reads structured JSON input (array of papers with nested references). Exports `verify_references()` as a reusable function for programmatic use. Outputs `results.json` and `results.txt`.

### End-to-end orchestrator (`run_pipeline.py`)

Connects PDF extraction to the full postprocessing pipeline. Takes a directory of PDFs (`-d`), extracts references, verifies them, classifies scholarly vs grey literature, and exports hallucination candidates for LLM verification. All output goes to `--output-dir`.

### Pipeline flow

Each script reads the previous script's output file by convention:
- `check_references_from_json.py` → writes `results.json`
- `postprocess_results.py` reads `results.json` → writes `results-filtered-postprocessed.json` (scholarly + not_found only)
- `export_for_llm_verification.py` reads `results-filtered-postprocessed.json` → writes `hallucination-candidates-for-verification.txt`
- `merge_llm_verdicts.py` reads manually-saved LLM output `.md` files → writes `merged-verdicts.md`

### Key data model

Reference statuses from database verification: `verified`, `author_mismatch`, `not_found`.

Classification types from postprocessing: `scholarly_candidate`, `standard_or_spec`, `industry_report`, `grey_spec`. Only `scholarly_candidate` + `not_found` are treated as true hallucination candidates.

LLM verdicts: `VERIFIED`, `DUBIOUS`, `CONFIRMED_HALLUCINATION`. Merge script sorts by severity (two CONFIRMED > one CONFIRMED > two DUBIOUS > one DUBIOUS > all VERIFIED).

### Reference ID format

`[ICSA_2026_paper_XXX_RY]` where XXX is the paper number from the PDF filename and Y is the reference index within that paper. Used to trace LLM verdicts back to source manuscripts.

## Important patterns

- Database query order matters: OpenAlex → CrossRef → arXiv → DBLP. DBLP is queried last with a configurable sleep delay (`--sleep`) to avoid rate limiting.
- Title matching uses `normalize_title()` which strips all non-alphanumeric characters. Author matching uses `validate_authors()` with rapidfuzz for fuzzy last-name comparison.
- PDF text extraction handles ligatures (fi, fl, ffi etc.) and hyphenation across line breaks, distinguishing syllable breaks from compound words (e.g., "human-centered").
- `postprocess_results()` and `export_for_llm()` accept an optional `output_dir` parameter; without it they write to the current directory.
- `--no-color` or `--output` flags disable ANSI color codes. The `Colors` class uses a `disable()` classmethod that blanks all color constants.
