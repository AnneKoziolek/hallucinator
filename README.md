# Hallucinated Reference Detector

A tool to detect potentially hallucinated or fabricated references in academic PDF papers. It extracts references from PDFs and validates them against academic databases (CrossRef, arXiv, DBLP, and optionally OpenAlex).

Created by Gianluca Stringhini with the help of Claude Code and ChatGPT

## Features

- **End-to-end pipeline**: point it at a folder of PDFs and get a verification report
- Pure Python PDF reference extraction using PyMuPDF (no external services required)
- Supports multiple citation formats:
  - IEEE (quoted titles)
  - ACM (year before title)
  - USENIX (author-title-venue format)
- Validates references against multiple academic databases (in order):
  - OpenAlex (optional, with API key)
  - CrossRef
  - arXiv
  - DBLP
- Classifies references as scholarly vs grey literature (standards, industry reports, specs)
- Exports suspected hallucinations with a ready-to-paste prompt for LLM verification
- Author matching to detect title matches with wrong authors
- Colored terminal output for easy identification of issues
- Handles em-dash citations (same authors as previous reference)

## Installation

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

Place your PDF files in a `papers/` directory (or any directory of your choice), then run:

```bash
source venv/bin/activate

# Run the full pipeline
python3 run_pipeline.py -d papers/ --sleep=0.5 --output-dir=output/

# With OpenAlex API key for better database coverage (optional)
python3 run_pipeline.py -d papers/ --openalex-key=YOUR_API_KEY --sleep=0.5 --output-dir=output/
```

This will:
1. Extract references from every PDF in the directory
2. Verify each reference against OpenAlex, CrossRef, arXiv, and DBLP
3. Classify references as scholarly vs grey literature (standards, industry reports, etc.)
4. Export suspected hallucinations to a text file with a ready-to-paste LLM prompt

### Pipeline options

| Option | Default | Description |
|--------|---------|-------------|
| `-d`, `--pdf-dir` | `papers/` | Directory containing PDF files |
| `--openalex-key` | *(none)* | OpenAlex API key for enhanced metadata |
| `--sleep` | `0.5` | Seconds to wait between DBLP queries (rate limiting) |
| `--output-dir` | `output/` | Directory for all output files |

### Output files

After the pipeline runs, the output directory will contain:

| File | Description |
|------|-------------|
| `results.json` | Full verification results for every reference |
| `results-postprocessed.json` | All results with scholarly/grey literature classification |
| `results-filtered-postprocessed.json` | Only scholarly references that were not found (true hallucination candidates) |
| `report-postprocessed.txt` | Human-readable classification statistics |
| `hallucination-candidates-for-verification.txt` | Formatted list with LLM prompt template for manual verification |

### What to do with the results

1. Open `output/hallucination-candidates-for-verification.txt`
2. Copy the **"PROMPT TEMPLATE FOR LLM VERIFICATION"** section at the bottom
3. Paste it into ChatGPT (with web search enabled) or Claude
4. Save the LLM's response to a `.md` file, e.g. `output/llm-run1.md`
5. Optionally repeat with a second LLM run and merge the results:

```bash
python3 merge_llm_verdicts.py output/merged-verdicts.md output/llm-run1.md output/llm-run2.md
```

The merge script sorts results by severity: confirmed hallucinations first, then dubious, then verified.

The LLM response must use the format `[ref_id] VERDICT | explanation` (one per line), where VERDICT is `VERIFIED`, `DUBIOUS`, or `CONFIRMED_HALLUCINATION`. The prompt template already asks the LLM to use this format.

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Advanced: Running Individual Scripts

The pipeline is composed of individual scripts that can also be run separately.

### Checking a single PDF directly

```bash
python3 check_hallucinated_references.py <path_to_pdf>

# Options
python3 check_hallucinated_references.py --no-color <path_to_pdf>
python3 check_hallucinated_references.py --output log.txt <path_to_pdf>
python3 check_hallucinated_references.py --sleep=0.5 <path_to_pdf>
```

Note: this outputs text only (no JSON), so the downstream pipeline scripts cannot consume its output directly. Use `run_pipeline.py` for the full end-to-end workflow.

### Checking references from JSON (pre-extracted)

If you have references already extracted by another tool in JSON format:

```bash
python3 check_references_from_json.py <json_file>
python3 check_references_from_json.py --openalex-key=YOUR_API_KEY --sleep=0.5 <json_file>
```

Expected JSON input format:

```json
[
  {
    "pdf": "papers/paper_1.pdf",
    "references": [
      {
        "title": "Paper title",
        "authors": ["J Smith", "A Jones"],
        "year": "2023",
        "doi": null,
        "verification": { "exists": false, "reason": "score_below_threshold" }
      }
    ]
  }
]
```

### Post-processing, export, and merge (manual steps)

```bash
# Classify scholarly vs grey literature
python3 postprocess_results.py results.json

# Export hallucination candidates for LLM verification
python3 export_for_llm_verification.py results-filtered-postprocessed.json

# Merge multiple LLM verification runs
python3 merge_llm_verdicts.py merged-verdicts.md run1.md run2.md
```

## Scripts Summary

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `run_pipeline.py` | PDF directory | All output files | **End-to-end pipeline** |
| `check_hallucinated_references.py` | Single PDF | Console + text logs | Extract & verify references from one PDF |
| `check_references_from_json.py` | JSON (pre-extracted refs) | `results.json` | Verify pre-extracted references |
| `postprocess_results.py` | `results.json` | Classified JSON + report | Classify references by type |
| `export_for_llm_verification.py` | Filtered JSON | Verification prompt text | Format for LLM verification |
| `merge_llm_verdicts.py` | Multiple `.md` files | `merged-verdicts.md` | Merge and compare LLM results |

## How It Works

1. **PDF Text Extraction**: Uses PyMuPDF to extract text from the PDF
2. **Reference Section Detection**: Locates the "References" or "Bibliography" section
3. **Reference Segmentation**: Splits references by numbered patterns ([1], [2], etc.)
4. **Title & Author Extraction**: Parses each reference to extract title and authors
5. **Database Validation**: Queries databases in order of rate-limit generosity:
   - OpenAlex (if API key provided) — most generous rate limits
   - CrossRef — good coverage, generous limits
   - arXiv — moderate limits
   - DBLP — most restrictive, queried last with configurable delay
6. **Author Matching**: Confirms that found titles have matching authors
7. **Classification**: Separates scholarly references from grey literature (standards, industry reports, specs) so only true hallucination candidates are flagged
8. **LLM Export**: Formats candidates with a prompt template ready to paste into ChatGPT or Claude for web-search verification

## Limitations

- References to non-indexed sources (technical reports, websites, books) may be flagged as "not found" — the classification step filters most of these out
- Very recent papers may not yet be indexed in databases
- Some legitimate papers in niche journals may not be found
- PDF extraction quality depends on the PDF structure

## Dependencies

- `requests` — HTTP requests for API queries
- `beautifulsoup4` — HTML parsing
- `rapidfuzz` — Fuzzy string matching for title comparison
- `feedparser` — arXiv API response parsing
- `PyMuPDF` — PDF text extraction
- `pytest` — Testing

## License

MIT License
