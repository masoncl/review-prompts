Read the prompt REVIEW_DIR/review-core.md

This performs deep dive regression analysis of an entire patch series (git range).

## Usage

Basic usage with git range:
```
/kseries base_commit..head_commit
```

With cover letter message-id (recommended for posted series):
```
/kseries base_commit..head_commit --cover-letter <message-id>
```

Or provide the full lore URL:
```
/kseries base_commit..head_commit --cover-letter https://lore.kernel.org/list/message-id/
```

If no message-id is provided, the command will attempt to find the cover letter
automatically using semcode lore integration (if available).

## Series Analysis Workflow

### PHASE 0: Series Overview and Context

1. Extract the list of commits in the series using git log
   - Print the series in commit order (oldest first) in the format: #. <commit hash> <commit subject>
   - Identify the total number of commits in the series

2. Retrieve and analyze the cover letter (if available):

   **Option A: If message-id provided by user**
   - Use the provided message-id to fetch the cover letter directly
   - Via lore website URL: `https://lore.kernel.org/<list>/<message-id>/`
   - Via semcode lore MCP: `lore_search(message_id="<id>", verbose=true)`

   **Option B: If no message-id provided, search for cover letter**
   - Use semcode lore if available: `dig(commit="<first-commit-in-series>", show_all=true)`
   - Look for `[PATCH 0/N]` or `[PATCH vX 0/N]` in the subject lines
   - If found, fetch the cover letter with: `lore_search(message_id="<id>", verbose=true)`

   **Option C: No lore access or cover letter not found**
   - Proceed without cover letter context
   - Note in output: "Cover letter: not found / not available / not provided"

   **Cover letter analysis:**
   - Extract the series goals and motivation
   - Note any design decisions or trade-offs mentioned
   - Identify testing done (what was tested, how, what wasn't tested)
   - Note any known issues or limitations acknowledged
   - Extract performance claims or behavioral changes
   - Identify subsystem maintainer feedback (if cover letter is a reply)
   - Look for references to prior discussions or related work

   **Output:**
   ```
   === COVER LETTER ANALYSIS ===
   Found: <yes/no>
   Source: <message-id or URL or "not available">
   Version: <v1/v2/v3/etc if present>

   Series goals: <summary from cover letter>
   Design decisions: <key points>
   Testing performed: <summary>
   Known issues: <list or "none mentioned">
   Performance/behavior changes: <summary or "none">
   ```

3. Analyze the series as a whole:
   - Read all commit messages to understand the overall goals
   - Cross-reference with cover letter goals (if available)
   - Identify the subsystems affected
   - Determine if this is a feature series, bug fix series, or refactoring series
   - Identify dependencies between commits (does commit N+1 build on commit N?)
   - Note any patterns across the series (e.g., "first 3 commits are prep work, next 2 are the feature")
   - Check if commit messages align with cover letter narrative

4. Output series context:
   ```
   === SERIES ANALYSIS ===
   Range: <base>..<head>
   Total commits: <N>
   Primary subsystem(s): <list>
   Series type: <feature/bugfix/refactor/mixed>
   Series goal: <one-line summary>

   Commit structure:
   1. <sha> <subject> - <purpose in series>
   2. <sha> <subject> - <purpose in series>
   ...
   ```

### PHASE 1: Commit-by-Commit Deep Dive

For each commit in the series (in chronological order):

1. **Mark the current commit** being analyzed with an asterisk in the series list

2. **Provide series context** for this commit:
   - Which commits come before this one in the series
   - Which commits come after this one in the series
   - How this commit relates to the overall series goals (from cover letter if available)
   - How this commit relates to the cover letter narrative (if available)
   - Any dependencies from previous commits in the series

3. **Execute full review-core.md protocol** for this single commit:
   - Load all required files (technical-patterns.md, subsystem guides, etc.)
   - Follow ALL tasks from review-core.md (Task 0 through Task 5)
   - When checking for fixes/regressions, consider:
     * Forward fixes: Are regressions introduced here fixed by later commits in the series?
     * Series-wide patterns: Does this commit make assumptions that later commits break?
   - Create review-inline.txt and review-metadata.json for THIS commit if regressions found
   - Output FINAL REGRESSIONS FOUND for this commit

4. **Series-aware regression checking**:
   - If a regression is found, check if it's fixed by a later commit in the series
   - If fixed within the series, note it but consider if it should have been squashed
   - Check if this commit breaks invariants that earlier commits in the series depend on
   - Verify commit ordering: should this commit come before/after others in the series?

5. Output commit completion:
   ```
   === COMMIT N/TOTAL COMPLETE ===
   Commit: <sha> <subject>
   Regressions found: <count>
   Fixed by later commits in series: <count>
   Series ordering issues: <yes/no>
   ```

### PHASE 2: Series-Wide Analysis

After analyzing all individual commits:

1. **Cross-commit regression check**:
   - Do early commits introduce regressions that later commits fix?
   - Should any commits be squashed together?
   - Are commits in the wrong order?
   - Are there missing commits (e.g., a fix is needed but not present)?

2. **Series cohesion check**:
   - Does the series accomplish its stated goal?
   - Are all commits necessary?
   - Are there orphaned changes that don't relate to the series goal?
   - Should this be split into multiple series?

3. **Cover letter verification** (if cover letter was found):
   - Do the commits accomplish the goals stated in the cover letter?
   - Are design decisions from the cover letter actually implemented?
   - Verify testing claims: does the code match what was claimed to be tested?
   - Check known issues: are they actually handled/documented in the code?
   - Verify performance/behavior claims: do the changes match the description?
   - Are there discrepancies between cover letter and implementation?
   - Output any mismatches as potential issues

4. **Final series report**:
   ```
   === SERIES REVIEW COMPLETE ===
   Total commits analyzed: <N>
   Commits with regressions: <count>
   Regressions fixed within series: <count>
   Regressions unfixed: <count>
   Series structure issues: <list or "none">

   Overall series assessment: <GOOD/NEEDS_WORK/BROKEN>
   ```

## Output Files

For each commit with regressions:
- `<sha>/review-inline.txt` - Detailed regression report
- `<sha>/review-metadata.json` - Metadata for that commit

For the series as a whole:
- `series-summary.txt` - Summary of all findings across the series, including cover letter analysis
- `series-metadata.json` - Aggregated metadata including cover letter source
- `series-cover-letter.txt` - The retrieved cover letter (if found)

## Important Notes

- Each commit is analyzed with the FULL depth of review-core.md
- Don't skip Task 2.1 (commit tag verification) even for series commits
- Series context should inform but not override individual commit analysis
- A regression fixed later in the series is still a regression (bisection will find it)
- Consider whether commits should be reordered or squashed as part of the review
- Cover letter analysis provides crucial context but should not prevent finding bugs
- If cover letter claims are contradicted by the code, report it as a regression
- Save the cover letter to `series-cover-letter.txt` for later reference
