# Complete Reference Verification Workflow

This document describes the complete end-to-end workflow for detecting and verifying hallucinated references in academic papers.

## Workflow Overview

```
Input JSON (filtered.json)
         ↓
  [Step 1: Verification]
  check_references_from_json.py
  (OpenAlex, CrossRef, arXiv, DBLP)
         ↓
    results.json
         ↓
  [Step 2: Classification]
  postprocess_results.py
  (scholarly vs grey literature)
         ↓
results-filtered-postprocessed.json
  (65 scholarly hallucination candidates)
         ↓
  [Step 3: LLM Export]
  export_for_llm_verification.py
         ↓
hallucination-candidates-for-verification.txt
         ↓
  [Step 4: Manual Verification]
  ChatGPT/Claude with web search
         ↓
chatGPT-output-*.md (multiple runs)
         ↓
  [Step 5: Merge Results]
  merge_llm_verdicts.py
         ↓
   merged-verdicts.md
   (sorted by verdict severity)
```

## Step 1: Verify References Against Academic Databases

Run the Python hallucinator script to check references against multiple databases:

```bash
cd /home/anne/ReferenceChecker/hallucinator

python3 check_references_from_json.py \
  --openalex-key=YOUR_API_KEY \
  --sleep=0.5 \
  filtered.json
```

**Input Format:**
```json
[
  {
    "pdf": "papers/ICSA_2026_paper_1.pdf",
    "references": [
      {
        "title": "Paper Title",
        "authors": ["Author1", "Author2"],
        "year": "2020"
      }
    ]
  }
]
```

**Outputs:**
- `results.json` - Structured JSON with verification details
- `results.txt` - Human-readable progress log

**Verification Process:**
1. Query OpenAlex (if API key provided)
2. Query CrossRef (if not found in OpenAlex)
3. Query arXiv (if not found)
4. Query DBLP (if not found, with rate limiting)
5. Validate authors using fuzzy matching

**Status Values:**
- `verified`: Reference found with matching authors
- `author_mismatch`: Title found but authors don't match
- `not_found`: Not found in any database

**Example Results (388 references):**
- Verified: 255 (65.7%)
- Author Mismatch: 47 (12.1%)
- Not Found: 86 (22.2%)

## Step 2: Classify References by Type

Filter out grey literature (standards, industry reports, etc.) to focus on true scholarly hallucinations:

```bash
python3 postprocess_results.py results.json
```

**Classification Heuristics:**
- **Standards/Specifications**: IEEE, ISO, AUTOSAR, W3C, IETF, etc.
- **Industry Reports**: McKinsey, Gartner, Forrester, etc.
- **Grey Literature**: Keywords like "specification", "white paper", "standard"
- **Domain Patterns**: URLs, .org, .com domains
- **Version Patterns**: R21.11, v2.0, etc.
- **Organizational Authors**: Single-word or institute-like names

**Outputs:**
- `results-postprocessed.json` - All results with classification
- `results-filtered-postprocessed.json` - Only scholarly + not_found (true hallucinations)
- `report-postprocessed.txt` - Statistics and analysis

**Example Results (from 86 not_found):**
- Standard/Spec: 4 references
- Industry Report: 3 references
- Grey Literature: 16 references
- **Scholarly Candidates: 65 references** ← True hallucination suspects

## Step 3: Export for LLM Verification

Format the scholarly hallucination candidates for verification with ChatGPT/Claude:

```bash
python3 export_for_llm_verification.py results-filtered-postprocessed.json
```

**Output:**
- `hallucination-candidates-for-verification.txt` (625 lines, 65 references)

**File Structure:**
1. **PAPER SOURCES** - Maps paper IDs to file paths
   ```
   ICSA_2026_paper_101: papers/ICSA_2026_paper_101.pdf
   ICSA_2026_paper_104: papers/ICSA_2026_paper_104.pdf
   ```

2. **QUICK REFERENCE LIST** - All references with IDs
   ```
   [ICSA_2026_paper_101_R1] "Title" by Authors (Year)
   [ICSA_2026_paper_107_R2] "Title" by Authors (Year)
   ```

3. **PROMPT TEMPLATE FOR LLM VERIFICATION** - Ready to paste into ChatGPT

**Reference ID Format:**
- `[ICSA_2026_paper_XXX_RY]`
  - `ICSA_2026_paper_XXX` = Paper filename (for manuscript lookup)
  - `RY` = Reference number within that paper
  - Example: `ICSA_2026_paper_107_R2` = Reference #2 from paper 107

## Step 4: Manual LLM Verification

1. Open `hallucination-candidates-for-verification.txt`
2. Copy the "PROMPT TEMPLATE FOR LLM VERIFICATION" section
3. Paste into ChatGPT (GPT-4) or Claude with web search enabled
4. Save response to a markdown file (e.g., `chatGPT-output-run1.md`)
5. **Recommended**: Run verification 2-3 times to check consistency
6. Save each run to separate files: `chatGPT-output-run1.md`, `chatGPT-output-run2.md`

**Expected Response Format:**
```
[ICSA_2026_paper_101_R1] DUBIOUS | Explanation...
[ICSA_2026_paper_107_R2] CONFIRMED_HALLUCINATION | Not found anywhere
[ICSA_2026_paper_109_R1] VERIFIED | Found in arXiv
```

**Verdict Categories:**
- `VERIFIED`: Paper exists and is correctly cited
- `DUBIOUS`: Paper exists but has errors in title/authors/year
- `CONFIRMED_HALLUCINATION`: Paper cannot be found anywhere

## Step 5: Merge Multiple Verification Runs

Compare results from multiple LLM runs to identify high-confidence hallucinations:

```bash
python3 merge_llm_verdicts.py merged-verdicts.md \
  chatGPT-output-run1.md \
  chatGPT-output-run2.md
```

**Outputs:**
- `merged-verdicts.md` - All references with all verdicts, sorted by severity

**Sorting Priority:**
1. **Two CONFIRMED_HALLUCINATION** (15 references) - Highest confidence
2. **At least one CONFIRMED_HALLUCINATION** (14 references) - Likely hallucinations
3. **Two DUBIOUS** (9 references) - Uncertain citations
4. **At least one DUBIOUS** (7 references) - Some concerns
5. **All VERIFIED** (20 references) - References appear valid

**Example Output:**
```markdown
[ICSA_2026_paper_28_R1]
  File 1: CONFIRMED_HALLUCINATION | No credible match found
  File 2: CONFIRMED_HALLUCINATION | Could not find this paper

[ICSA_2026_paper_107_R1]
  File 1: DUBIOUS | Found as grey literature
  File 2: CONFIRMED_HALLUCINATION | Could not find
```

## Understanding the Results

### High-Confidence Hallucinations
References with **two CONFIRMED_HALLUCINATION verdicts** are the strongest candidates for fabricated references.

**Example from paper 28 (6 hallucinations detected):**
- Paper has 6 references that both ChatGPT runs could not verify
- All references are about UML model evaluation and generation
- Pattern suggests systematic fabrication around a specific topic

### Grey Literature vs Scholarly Papers
The classification step filters out legitimate grey literature:
- **Standards**: IEEE standards, ISO specifications (not hallucinations)
- **Industry Reports**: McKinsey reports, Gartner papers (not hallucinations)
- **Blog Posts**: Simon Brown's C4 Model (valid citation, not scholarly)

### Tracing Back to Papers
Use the paper ID to find the source manuscript:
- `ICSA_2026_paper_107_R2` → Paper 107 is at `papers/ICSA_2026_paper_107.pdf`
- Reference 2 within that paper is a confirmed hallucination
- Authors can be contacted or paper rejected based on findings

## Performance and Scale

**Timing (388 references):**
- Step 1 (Verification): ~6-13 minutes (1-2 sec per reference)
- Step 2 (Classification): < 1 second
- Step 3 (Export): < 1 second
- Step 4 (LLM): 5-10 minutes per run (manual)
- Step 5 (Merge): < 1 second

**Total Time:** ~30-40 minutes for complete workflow

**Resource Usage:**
- OpenAlex API: Free tier supports this workflow
- ChatGPT: Standard subscription with web search required
- Disk space: ~5 MB for all intermediate files

## Best Practices

### 1. Run LLM Verification Multiple Times
- Run ChatGPT verification 2-3 times
- Compare results to identify consistent hallucinations
- LLMs may give different verdicts on ambiguous cases

### 2. Review High-Priority Cases First
- Start with "Two CONFIRMED_HALLUCINATION" (highest confidence)
- Check paper patterns (e.g., paper 28 has 6 hallucinations)
- Contact authors for papers with multiple confirmed hallucinations

### 3. Consider Context
- Grey literature is not necessarily wrong (standards, specs, reports)
- Blog posts and industry documents may be intentionally cited
- Focus on scholarly papers that appear to be fabricated

### 4. Preserve Evidence
- Keep all intermediate files (`results.json`, `chatGPT-output-*.md`)
- Document verification process for reproducibility
- Include LLM verification timestamps and model versions

### 5. Handle Edge Cases
- Very recent papers (2025-2026) may not be indexed yet
- Preprints may not have stable bibliographic records
- Non-English papers may have indexing issues

## File Locations

```
/home/anne/ReferenceChecker/hallucinator/
├── check_references_from_json.py        (Step 1: Verification)
├── postprocess_results.py               (Step 2: Classification)
├── export_for_llm_verification.py       (Step 3: LLM Export)
├── merge_llm_verdicts.py                (Step 5: Merge Results)
├── results.json                         (Verification output)
├── results-postprocessed.json           (Classification output)
├── results-filtered-postprocessed.json  (65 scholarly candidates)
├── hallucination-candidates-for-verification.txt
├── chatGPT-output-run1.md              (LLM verification run 1)
├── chatGPT-output-run2.md              (LLM verification run 2)
└── merged-verdicts.md                  (Final results)
```

## Example: Complete Workflow Execution

```bash
# Navigate to project
cd /home/anne/ReferenceChecker/hallucinator

# Step 1: Verify references (6-13 minutes)
python3 check_references_from_json.py \
  --openalex-key=YOUR_KEY \
  --sleep=0.5 \
  filtered.json
# → results.json (388 references: 255 verified, 86 not found)

# Step 2: Classify by type (< 1 second)
python3 postprocess_results.py results.json
# → results-filtered-postprocessed.json (65 scholarly candidates)

# Step 3: Export for LLM (< 1 second)
python3 export_for_llm_verification.py results-filtered-postprocessed.json
# → hallucination-candidates-for-verification.txt (625 lines)

# Step 4: Manual LLM verification (5-10 minutes per run)
# - Copy prompt template to ChatGPT
# - Save to chatGPT-output-run1.md
# - Repeat for run 2

# Step 5: Merge results (< 1 second)
python3 merge_llm_verdicts.py merged-verdicts.md \
  chatGPT-output-run1.md \
  chatGPT-output-run2.md
# → merged-verdicts.md (sorted by severity)

# View high-confidence hallucinations
grep -A 5 "TWO CONFIRMED_HALLUCINATION" merged-verdicts.md | head -50
```

## Customization Options

### Adjust Database Query Delay
```bash
# Slower (more conservative with DBLP rate limits)
python3 check_references_from_json.py --sleep=2.0 filtered.json

# Faster (if you have API access or smaller dataset)
python3 check_references_from_json.py --sleep=0.1 filtered.json
```

### Disable Colored Output
```bash
python3 check_references_from_json.py --no-color filtered.json
```

### Change Classification Thresholds
Edit `postprocess_results.py` to adjust heuristics:
- Add new standards organizations
- Add new industry report sources
- Modify keyword patterns
- Adjust confidence levels

### Merge More Than 2 Runs
```bash
python3 merge_llm_verdicts.py merged-verdicts.md \
  run1.md run2.md run3.md run4.md
```

## Troubleshooting

### Issue: OpenAlex Rate Limiting
**Solution**: Increase `--sleep` parameter or get API key from https://openalex.org/settings/api

### Issue: DBLP Returns Too Many 503 Errors
**Solution**: Increase `--sleep=2.0` or higher for DBLP queries

### Issue: LLM Gives Inconsistent Verdicts
**Solution**: Run verification 3+ times and use majority vote for final verdict

### Issue: Too Many "Not Found" Results
**Solution**: Check if your input JSON has correct titles/authors; run classification to filter grey literature

### Issue: Classification Misses Grey Literature
**Solution**: Update heuristics in `postprocess_results.py` with new patterns

## Future Enhancements

Possible improvements to the workflow:

1. **Automated LLM Integration**: Call OpenAI API directly instead of manual copy-paste
2. **Voting System**: Automatically combine multiple LLM runs with majority voting
3. **PDF Report Generation**: Generate PDF reports with hallucination findings
4. **Database Expansion**: Add Google Scholar, Semantic Scholar, Microsoft Academic
5. **Citation Context**: Extract citation context from PDFs for verification
6. **Author Contact**: Generate templated emails to authors with findings
