# Hallucinated Reference Detector

A tool to detect potentially hallucinated or fabricated references in academic PDF papers. It extracts references from PDFs and validates them against academic databases (CrossRef, arXiv, DBLP, and optionally OpenAlex).

Created by Gianluca Stringhini with the help of Claude Code and ChatGPT

## Features

- Pure Python PDF reference extraction using PyMuPDF (no external services required)
- **Citation sentence extraction**: Extracts and displays the sentences where each reference is cited in the paper
- Supports multiple citation formats:
  - IEEE (quoted titles)
  - ACM (year before title)
  - USENIX (author-title-venue format)
- Validates references against multiple academic databases (in order):
  - OpenAlex (optional, with API key)
  - CrossRef
  - arXiv
  - DBLP
- Author matching to detect title matches with wrong authors
- Colored terminal output for easy identification of issues
- Handles em-dash citations (same authors as previous reference)
- Comprehensive unit tests for citation extraction logic


## Installation

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Checking PDFs directly

```bash
# Basic usage
python check_hallucinated_references.py <path_to_pdf>

# Without colored output (for piping or non-color terminals)
python check_hallucinated_references.py --no-color <path_to_pdf>

# Save output to file
python check_hallucinated_references.py --output log.txt <path_to_pdf>

# Adjust delay before DBLP requests (default: 1 second, to avoid rate limiting)
python check_hallucinated_references.py --sleep=0.5 <path_to_pdf>

### Checking references from JSON (from reference verification pipeline)

The `check_references_from_json.py` script processes references that have already been extracted and verified by another tool, reading a JSON file with structured reference data:

```bash
# Basic usage
python check_references_from_json.py <json_file>

# Without colored output
python check_references_from_json.py --no-color <json_file>

# With OpenAlex API key (for better coverage)
python check_references_from_json.py --openalex-key=YOUR_API_KEY <json_file>

# With custom delay for DBLP
python check_references_from_json.py --sleep=2.0 <json_file>
```

### Post-processing: Classifying references by type

After verification, use `postprocess_results.py` to classify references by type (scholarly vs grey literature):

```bash
python postprocess_results.py results.json
```

This outputs:
- `results-postprocessed.json` - All results with classification
- `results-filtered-postprocessed.json` - Only scholarly + not_found (true hallucinations)
- `report-postprocessed.txt` - Classification statistics

### Exporting for LLM verification

To verify suspected hallucinations using an LLM (ChatGPT, Claude, etc.) with web search:

```bash
python3 export_for_llm_verification.py results-filtered-postprocessed.json
```

This creates:
- `hallucination-candidates-for-verification.txt` - Formatted list ready for LLM verification
  - Contains: title, authors, year for each suspected hallucination
  - References formatted with paper IDs (e.g., `ICSA_2026_paper_107_R2`)
  - Includes prompt template for ChatGPT/Claude
  - Paper ID mapping section to trace back to source manuscripts

**Reference ID Format:**
Each reference uses format `[ICSA_2026_paper_XXX_RY]` where:
- `ICSA_2026_paper_XXX` = Paper filename (for easy manuscript lookup)
- `RY` = Reference number within that paper

### Merging multiple LLM verification runs

After getting verification results from ChatGPT/Claude, merge and compare results:

```bash
python3 merge_llm_verdicts.py merged-verdicts.md file1.md file2.md
```

This creates:
- `merged-verdicts.md` - Sorted by verdict severity:
  1. Two CONFIRMED_HALLUCINATION (highest confidence)
  2. At least one CONFIRMED_HALLUCINATION
  3. Two DUBIOUS
  4. At least one DUBIOUS
  5. All VERIFIED
- Shows both verdicts side-by-side for comparison
- Includes reference IDs for tracing back to papers

## Complete Workflow Example

From raw references to verified hallucinations:

```bash
# Step 1: Verify references against academic databases
python3 check_references_from_json.py \
  --openalex-key=YOUR_API_KEY \
  --sleep=0.5 \
  filtered.json
# Output: results.json, results.txt

# Step 2: Classify references by type (scholarly vs grey literature)
python3 postprocess_results.py results.json
# Output: results-postprocessed.json, results-filtered-postprocessed.json, report-postprocessed.txt

# Step 3: Export true hallucination candidates for LLM verification
python3 export_for_llm_verification.py results-filtered-postprocessed.json
# Output: hallucination-candidates-for-verification.txt

# Step 4: Verify in ChatGPT/Claude
# Copy the "PROMPT TEMPLATE FOR LLM VERIFICATION" section
# Paste into ChatGPT with web search enabled
# Save results to chatGPT-output1.md and chatGPT-output2.md

# Step 5: Merge multiple LLM verification runs
python3 merge_llm_verdicts.py merged-verdicts.md \
  chatGPT-output1.md \
  chatGPT-output2.md
# Output: merged-verdicts.md (sorted by verdict severity)
```

### Results

- **Verification**: 388 references → 255 verified, 133 problematic
- **Classification**: 133 problematic → 65 scholarly (true hallucinations), 68 grey literature
- **LLM Verification**: 65 candidates ready for manual verification with web search
- **Merged Results**: Side-by-side comparison of multiple verification runs

## Scripts Summary

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `check_hallucinated_references.py` | PDF file | Console + logs | Extract & verify references from PDFs |
| `check_references_from_json.py` | JSON (references) | results.json | Verify pre-extracted references |
| `postprocess_results.py` | results.json | results-postprocessed.json | Classify references by type |
| `export_for_llm_verification.py` | results-filtered-postprocessed.json | hallucination-candidates-for-verification.txt | Format for LLM verification |
| `merge_llm_verdicts.py` | Multiple .md files | merged-verdicts.md | Merge and compare LLM verification results |

### Checking references from JSON (from reference verification pipeline)

The `check_references_from_json.py` script processes references that have already been extracted and verified by another tool, reading a JSON file with the following format:

```json
[
  {
    "pdf": "papers/ICSA_2026_paper_X.pdf",
    "error": null,
    "reference_count": 30,
    "references": [
      {
        "title": "Some Title",
        "authors": ["J Chen", "V Nair", "R Krishna", "T Menzies"],
        "year": "2006",
        "doi": null,
        "verification": {
          "exists": false,
          "reason": "score_below_threshold"
        }
      }
    ]
  }
]
```

Usage:

```bash
# Basic usage
python check_references_from_json.py <json_file>

# Without colored output
python check_references_from_json.py --no-color <json_file>

# Save output to file
python check_references_from_json.py --output results.txt <json_file>

# With OpenAlex API key
python check_references_from_json.py --openalex-key=YOUR_API_KEY <json_file>

# With custom delay for DBLP
python check_references_from_json.py --sleep=2.0 <json_file>
```

### Options

| Option | Description |
|--------|-------------|
| `--no-color` | Disable colored output (useful for piping or logging) |
| `--sleep=SECONDS` | Set delay before DBLP requests to avoid rate limiting (default: 1.0 second). Only applies when a reference isn't found in earlier databases. |
| `--openalex-key=KEY` | OpenAlex API key. If provided, queries OpenAlex first before other databases. Get a free key at https://openalex.org/settings/api |

## Example Output

```
Analyzing paper example.pdf

============================================================
POTENTIAL HALLUCINATION DETECTED
============================================================

Title:
  Some Fabricated Paper Title That Does Not Exist

Status: Reference not found in any database
Searched: CrossRef, arXiv, DBLP

Cited in these sentences:
  1. This approach was first proposed in [15] and has since been widely adopted.
  2. The results from [15] show significant improvement over baseline methods.

------------------------------------------------------------

============================================================
SUMMARY
============================================================
  Total references analyzed: 35
  Verified: 34
  Not found (potential hallucinations): 1
```

## Testing and Demonstration

### Running Unit Tests

The repository includes comprehensive unit tests for the citation sentence extraction functionality:

```bash
# Run all tests
python -m pytest test_citation_extraction.py -v

# Run specific test
python -m pytest test_citation_extraction.py::TestExtractCitationSentences::test_single_reference_single_sentence -v
```

### Citation Extraction Demo

To see how citation sentence extraction works without requiring a PDF:

```bash
python demo_citation_extraction.py
```

This demonstrates the extraction of citation sentences from sample academic text, showing:
- Which sentences cite each reference
- How many times each reference is cited
- Statistics about citation patterns

## How It Works

1. **PDF Text Extraction**: Uses PyMuPDF to extract text from the PDF
2. **Reference Section Detection**: Locates the "References" or "Bibliography" section
3. **Citation Sentence Extraction**: Finds and extracts sentences from the main text that cite each reference
   - Handles IEEE-style citations ([1], [2], etc.)
   - Properly handles author initials (M., J., etc.) when detecting sentence boundaries
   - Associates each citation marker with its containing sentence
4. **Reference Segmentation**: Splits references by numbered patterns ([1], [2], etc.)
5. **Title & Author Extraction**: Parses each reference to extract title and authors
6. **Database Validation**: Queries databases in order of rate-limit generosity:
   - OpenAlex (if API key provided) - most generous rate limits
   - CrossRef - good coverage, generous limits
   - arXiv - moderate limits
   - DBLP - most restrictive, queried last with configurable delay
7. **Author Matching**: Confirms that found titles have matching authors
8. **Citation Context Display**: Shows the sentences where problematic references are cited

## Limitations

- References to non-indexed sources (technical reports, websites, books) may be flagged as "not found"
- Very recent papers may not yet be indexed in databases
- Some legitimate papers in niche journals may not be found
- PDF extraction quality depends on the PDF structure

## Dependencies

- `requests` - HTTP requests for API queries
- `beautifulsoup4` - HTML parsing
- `rapidfuzz` - Fuzzy string matching for title comparison
- `feedparser` - arXiv API response parsing
- `PyMuPDF` - PDF text extraction

## License

MIT License
