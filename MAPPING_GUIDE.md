# Reference ID Mapping Guide

## How to Use the Updated Export

The `hallucination-candidates-for-verification.txt` file now includes paper and reference IDs to make it easy to map ChatGPT/LLM responses back to the original papers.

### Format

Each reference in the LLM prompt uses the format: `[P{paper_id}_R{reference_id}]`

Example: `[P1_R3]` means:
- **P1** = Paper ID 1 (see "PAPER ID MAPPING" section for full path)
- **R3** = Reference #3 within that paper

### How to Use It

1. **Locate the "PAPER ID MAPPING" section** at the top of the file
   - This shows which papers correspond to which P# IDs
   - Example: `P1: papers/ICSA_2026_paper_101.pdf`

2. **Copy the prompt template** and send to ChatGPT/Claude with web search

3. **Request responses in this format:**
   ```
   [P1_R1] VERIFIED | Exact match found
   [P1_R2] DUBIOUS | Title slightly different but same authors
   [P1_R3] CONFIRMED_HALLUCINATION | No paper found
   ```

4. **Map responses back:**
   - Response `[P2_R3] CONFIRMED_HALLUCINATION` = Reference 3 from Paper ID 2
   - Look up Paper ID 2 in the mapping: `papers/ICSA_2026_paper_104.pdf`

### Example Workflow

**Mapping section shows:**
```
P1: papers/ICSA_2026_paper_101.pdf
P2: papers/ICSA_2026_paper_104.pdf
P3: papers/ICSA_2026_paper_107.pdf
```

**LLM response:**
```
[P1_R1] VERIFIED | Found in arXiv
[P1_R2] CONFIRMED_HALLUCINATION | No such paper exists
[P2_R1] DUBIOUS | Authors are different
[P3_R1] VERIFIED | Found in IEEE Xplore
```

**You can now:**
1. Map back to source: P1_R2 is in `papers/ICSA_2026_paper_101.pdf`
2. Know which papers have hallucinated references
3. Potentially correct metadata in the original documents
4. Generate a summary report by paper

## Files Generated

- `hallucination-candidates-for-verification.txt` - Full export with:
  - Paper ID mapping at the top
  - References organized by paper
  - Quick reference list
  - Prompt template ready for LLM
  
- `results-filtered-postprocessed.json` - Structured JSON with classification (for programmatic post-processing)

- `report-postprocessed.txt` - Statistics and analysis

## Next Steps

1. Copy the "PROMPT TEMPLATE FOR LLM VERIFICATION" section
2. Paste into ChatGPT/Claude with web search enabled
3. Request verification with the format above
4. Save LLM responses to a file
5. Use the mapping to identify which papers have issues
