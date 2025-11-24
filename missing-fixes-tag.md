# Missing Fixes: Tag Detection

This prompt identifies commits that appear to fix bugs but lack a Fixes:
tag.

## Purpose

A Fixes: tag should be included when a patch fixes a bug in a previous
commit, even if the fix doesn't require stable backporting. Missing
Fixes: tags make it harder to:
- Track bug origins
- Determine stable backport scope
- Understand fix context during code review
- Correlate fixes with their original bugs

## Pattern-specific TodoWrite fields

Create a TodoWrite entry to track missing Fixes: tag detection:
- Commit has Fixes tag: [YES/NO]
- Subject line keywords: [list STRONG/MODERATE indicators found]
- Body bug indicators: [list indicators found or NONE]
- Code change patterns: [list bug fix patterns found or NONE]
- Stable tag present: [YES/NO]
- Reported-by present: [YES/NO]
- Link to bug tracker: [YES/NO - show link if present]
- Confidence level: [HIGH/MEDIUM/LOW]
- Recommendation: [should ask about Fixes tag / note only / no action]
- Reasoning: [explain the determination]

## When to Flag Missing Fixes: Tags [MISSING-FIXES-001]

**Risk**: Lost attribution, incomplete stable backports, poor git
archaeology

**Mandatory missing tag detection:**

Use TodoWrite to systematically evaluate the commit.

### 1. Subject Line Indicators

Check if the commit subject contains bug fix keywords and record in
TodoWrite:

**Strong indicators** (very likely a bug fix):
- fix, fixes, fixed, fixing
- crash, oops, panic, BUG
- deadlock, hang, lockup, stall
- corruption, corrupt
- leak, memory leak, refcount leak, use-after-free, UAF
- NULL pointer, null deref, null-ptr-deref
- race, race condition
- off-by-one, underflow, overflow
- regression
- revert (if reverting a bug, not just a feature)

**Moderate indicators** (might be a bug fix):
- correct, incorrect
- missing, add missing
- wrong, broken
- error, failure
- issue, problem

**Examples:**
- "mm: fix use-after-free in folio_put()" - STRONG indicator ✓
- "net: correct skb refcounting" - MODERATE indicator ⚠
- "bpf: add missing null check" - MODERATE indicator ⚠
- "fs: improve performance" - NOT a bug fix ✗

Record all indicators found in TodoWrite.

### 2. Commit Message Body Analysis

Check the commit description for bug-related language and record in
TodoWrite:

**Strong indicators:**
- "This fixes..."
- "This causes [crash/corruption/...]"
- "Without this patch..."
- References to reported bugs (bugzilla, syzkaller, etc.)
- Describes incorrect behavior being corrected
- Mentions user-visible regression
- "This broke when..." or "broke after commit..."

**Moderate indicators:**
- "This should..."
- "We need to..." (in context of correctness)
- Describes edge case handling

**Counter-indicators** (NOT bug fixes):
- Pure refactoring descriptions
- Performance optimization without correctness issue
- New feature additions
- Code cleanup
- Documentation updates

Record all indicators found in TodoWrite.

### 3. Code Change Pattern Analysis

Examine the actual changes for bug fix patterns and record in TodoWrite:

**Strong indicators:**
- Adding null/bounds checks that were missing
- Fixing lock imbalances (unlock without lock, etc.)
- Correcting reference counting (get without put, etc.)
- Reordering operations to fix races
- Fixing error path cleanup
- Adding missing error checks
- Correcting off-by-one errors
- Fixing memory leaks
- Initializing previously uninitialized variables
- Fixing use-after-free by reordering frees

**Moderate indicators:**
- Adding validation that was missing
- Changing condition logic
- Adjusting timeouts or thresholds

**Counter-indicators:**
- Pure code movement
- Renaming
- Adding new functionality
- Obvious refactoring

Record all patterns found in TodoWrite.

### 4. Context Clues

Check for additional evidence and record in TodoWrite:

- Cc: stable@vger.kernel.org tag (without Fixes: tag)
  - This is VERY suspicious - stable tag implies bug fix
- Reported-by: tags (bug reports usually mean bug fixes)
- Link: tags pointing to bug trackers
- References to syzbot, syzkaller, or other bug finders
- Mentions of specific kernel versions where bug appeared

Record all context clues in TodoWrite.

## Evaluation Framework [MISSING-FIXES-002]

**Mandatory evaluation process:**

Use this decision tree and record results in TodoWrite at each step:

```
1. Does subject contain STRONG bug fix keyword?
   YES → Record in TodoWrite, set confidence HIGH
         → Ask: "Should this have a Fixes: tag?"
   NO → Continue to step 2

2. Does subject contain MODERATE bug fix keyword?
   YES → Record in TodoWrite
         → Check commit body and code changes
         → Both suggest bug fix?
            Set confidence MEDIUM
            Ask: "Should this have Fixes: tag?"
         → Only one suggests bug fix?
            Set confidence LOW, note as possible
   NO → Continue to step 3

3. Does commit body describe fixing a bug?
   YES → Record in TodoWrite
         → Check code changes
         → Changes match bug fix pattern?
            Set confidence MEDIUM
            Ask: "Should this have Fixes: tag?"
   NO → Continue to step 4

4. Do code changes show strong bug fix patterns?
   YES → Record in TodoWrite
         → Check subject and body again
         → Describes a fix but no Fixes: tag?
            Set confidence MEDIUM
            Ask: "Should this have Fixes: tag?"
   NO → Continue to step 5

5. Is Cc: stable@vger.kernel.org present without Fixes: tag?
   YES → Record in TodoWrite, set confidence HIGH
         → ALWAYS ask: "Should this have Fixes: tag?"
   NO → Record: No Fixes: tag needed
```

Record each decision point in TodoWrite.

## Exception Cases [MISSING-FIXES-003]

**Mandatory exception validation:**

Do NOT flag as missing when (record in TodoWrite if applicable):

1. **Historical bugs**
   - Commit message notes "bug existed since initial implementation"
   - Bug predates git history
   - Commit references Linux 2.4 era or earlier

2. **Intentional omissions**
   - Commit message explicitly states why no Fixes: tag
   - Part of large refactoring series where individual commits are not
     standalone fixes

3. **Unclear causation**
   - Bug involves complex interaction of multiple commits
   - No single commit is clearly responsible
   - Root cause is architecture design, not specific commit

4. **Not actually bug fixes**
   - Hardening that doesn't fix specific bug
   - Adding error handling for theoretical future case
   - Preventive measures without existing bug

Record exception determination in TodoWrite.

## Confidence Levels

When flagging potentially missing Fixes: tags, indicate confidence in
TodoWrite:

**High confidence** (should definitely ask):
- STRONG keyword + bug description in body + bug fix code pattern
- Cc: stable present without Fixes: tag
- Reported-by: tag with clear bug report reference

**Medium confidence** (worth asking):
- MODERATE keyword + one of {bug description, bug fix pattern}
- STRONG keyword in subject but ambiguous description
- Clear bug fix pattern but vague commit message

**Low confidence** (mention as note):
- Only MODERATE keywords, unclear context
- Could be hardening rather than fixing
- Refactoring that happens to fix edge case

## Question Phrasing

When a Fixes: tag appears to be missing, phrase as a question:

**Good phrasing:**
- "This appears to fix a bug. Should it include a Fixes: tag?"
- "The commit mentions a crash/corruption/leak. Would a Fixes: tag be
  appropriate?"
- "This has Cc: stable but no Fixes: tag. What commit introduced the
  bug?"

**Avoid:**
- Accusatory phrasing
- Assuming intent
- Demanding changes

**Include context:**
- Quote the specific indicator (subject line keyword, commit message
  text, or code pattern)
- Explain why it looks like a bug fix
- Note if stable backporting seems intended

## Examples

### Clear Missing Fixes: Tag

```
Subject: mm: add missing null check in folio_put

The code crashes when folio is NULL.

[code shows adding: if (!folio) return;]
```
**Action**: Ask about missing Fixes: tag (HIGH confidence)
**TodoWrite**: STRONG keyword "crashes", adding null check pattern

### Probable Missing Fixes: Tag

```
Subject: net: correct reference counting

Cc: stable@vger.kernel.org

[code shows adding missing skb_get()]
```
**Action**: Ask about missing Fixes: tag (HIGH confidence - has stable
tag)
**TodoWrite**: Stable tag present, refcount fix pattern

### Possible Missing Fixes: Tag

```
Subject: bpf: improve error handling

This adds better validation to prevent issues.

[code shows adding bounds checks]
```
**Action**: Note as possible hardening vs. fix (LOW confidence)
**TodoWrite**: MODERATE indicators, unclear if fixing existing bug

### Not a Bug Fix

```
Subject: fs: refactor inode allocation

Consolidate three similar functions into one helper.

[code shows pure refactoring]
```
**Action**: No Fixes: tag needed
**TodoWrite**: Pure refactoring, no bug indicators

## Mandatory Self-verification gate

Before completing missing Fixes: tag detection, answer these questions:

**Pattern-specific questions:**
  1. Is there already a Fixes: tag in the commit message? [YES/NO]
  2. How many STRONG bug fix keywords found in subject? [number]
  3. How many MODERATE bug fix keywords found in subject? [number]
  4. How many bug indicators found in commit body? [number]
  5. How many bug fix code patterns found? [number]
  6. Is Cc: stable@vger.kernel.org present? [YES/NO]
  7. Is Reported-by: present? [YES/NO]
  8. Are there Links: to bug trackers? [YES/NO - list if present]
  9. What is the confidence level? [HIGH/MEDIUM/LOW]
 10. What is the recommendation? [ask about Fixes / note only / no
     action]
 11. Did you check for exception cases? [YES/NO - list if applicable]

If you cannot answer ALL questions with evidence, RESTART
missing-fixes-tag detection from the beginning.

## Integration with Review Process

This check should run:
- **After** Task 1 (commit message is known)
- **After** Task 2A (code changes are analyzed)
- **Before** Task 4 (reporting phase)

Add findings to the final report as questions about commit message
completeness.
