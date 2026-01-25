# Results Output Format

The `check_references_from_json.py` script now generates the following output files:

## 1. results.txt
A human-readable text file with:
- Progress indicators for each reference
- Database search progress (`→ Searching OpenAlex...`, etc.)
- Verification results with OpenAlex URLs for manual verification
- Summary statistics

## 2. results.json
A structured JSON file containing verification results for each reference. Each entry includes:

```json
{
  "title": "Original reference title",
  "authors": ["Author1", "Author2", ...],
  "year": "2016",
  "doi": null,
  "pdf": "papers/source_paper.pdf",
  "original_verification": {
    // Original verification data from input file
  },
  "hallucinator_check": {
    "status": "verified|author_mismatch|not_found",
    "source": "OpenAlex|CrossRef|arXiv|DBLP",
    "found_title": "Title found in database",
    "found_authors": ["Full Author Name", ...],
    "publication_year": 2016,
    "openalex_url": "https://openalex.org/W..."
  }
}
```

### Status Values:
- **verified**: Reference found with matching authors
- **author_mismatch**: Title found but authors don't match
- **not_found**: Reference not found in any database (potential hallucination)

### Use for Post-Processing:
You can use the `results.json` file for further analysis:
- Filter by status to identify problematic references
- Check OpenAlex URLs for manual verification
- Compare with original verification results
- Generate statistics and reports
- Feed into downstream tools for additional analysis

## Example Usage:
```bash
# With your OpenAlex API key
python3 check_references_from_json.py --openalex-key=YOUR_KEY filtered.json

# This creates:
# - results.txt (human-readable)
# - results.json (machine-readable, for post-processing)
```
