# Patch Size Analysis

Analyze the size and structure of the patch to ensure it is appropriately sized and conceptually atomic.

## Patch Size Classification
Calculate the total number of lines changed (sum of added and removed lines) in the `git diff` of the patch.
- **XS**: < 10 lines
- **S**: < 50 lines
- **M**: < 250 lines
- **L**: < 1000 lines
- **XL**: >= 1000 lines

For **XS** and **S** patches, the size is always considered appropriate.

## Structural Analysis
For **M**, **L**, and **XL** patches, perform the following analysis:

1. **Conceptual Integrity**:
   Analyze the patch to determine if all changes are conceptually related to a single goal.
   - Are there multiple unrelated bug fixes?
   - Is there a mix of refactoring and new functionality?
   - Are there changes to multiple distinct subsystems that could be separated?

2. **Decomposition Strategy**:
   If the patch contains conceptually distinct items, evaluate if it can be broken down into a series of smaller, atomic patches.
   - A decomposition is only valid if each resulting patch in the series would independently build and pass tests (assuming standard kernel CI).
   - Base functionality should be introduced first, followed by patches that build upon it.
   - Avoid introducing significant "glue" code or temporary scaffolding just to keep builds/tests running.

3. **80% Rule**:
   A patch is only considered "breakable" if it can be decomposed such that the largest resulting patch has a line delta that is less than **80%** of the original patch's total line delta.
   - If no such decomposition is possible while maintaining build/test integrity, report that the patch is **appropriately sized**.

## Reporting
If a decomposition is recommended, provide:
1. **Broken-down series description**: A clear list of suggested patches.
2. **Commit Messages**: Proposed commit messages for each new patch.
3. **Code Changes**: A summary or snippet of which parts of the original code changes belong to which new patch.

> [!IMPORTANT]
> When decomposition is recommended, the commit messages and code change summaries are MANDATORY. Do not just state that the patch should be broken up; you must provide the specific blueprint for how to do it.

If no decomposition is recommended (or possible under the 80% rule), explicitly state that the patch is appropriately sized.
