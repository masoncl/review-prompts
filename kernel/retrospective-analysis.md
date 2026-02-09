# Retrospective Analysis: Fixes: Tag Review

Determine if current prompts would have caught the bug when introduced.
Informational only--does not affect regression count.

## Conditions

- Commit has Fixes: tag
- Referenced commit accessible via git
- Subjective reviews enabled

## Procedure

1. **Retrieve original:** `git show <fixes-sha>` - read full diff and message

2. **Classify bug:** memory-safety | concurrency | resource-lifecycle | error-handling | logic | API-misuse | other

3. **List applicable prompts:** subsystem, pattern, and technical prompts that would load for original commit

4. **Assess each prompt:** Would its heuristics flag this bug? (YES/PARTIAL/NO with brief reasoning)

5. **Verdict:**
   - CAUGHT: at least one prompt has clear heuristics that would flag this bug
   - PARTIAL: prompts have related heuristics but bug requires inference
   - MISSED: no applicable heuristics would have detected this pattern

6. **If PARTIAL/MISSED:** Suggest specific heuristic addition (prompt, pattern, risk)

## Output Format

```
=== RETROSPECTIVE ANALYSIS ===
Fixes: <tag>
Original: <sha> <subject>
Category: <category>

Prompts: <list>

Analysis:
<prompt>: <YES/PARTIAL/NO> -- <reasoning>

VERDICT: <CAUGHT/PARTIAL/MISSED>

[SUGGESTED HEURISTIC: <prompt>, <pattern>, <risk>]
===
```

## Recording

Add to prompt improvement log (e.g., sunrpc/SUNRPC-007-updates.md):

| Fix | Fixes: | Category | Caught? |
|-----|--------|----------|---------|

## Notes

- Focus on whether heuristics exist, not perfect application
- Note bugs requiring dynamic analysis or domain expertise
