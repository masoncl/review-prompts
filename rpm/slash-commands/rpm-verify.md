---
name: rpm-verify
description: Verify findings against RPM packaging false positive patterns
---

Using the prompt {{REVIEW_DIR}}/false-positive-guide.md, verify that a
reported packaging issue is not a false positive.

This command helps validate potential issues found during spec file review
or rpmlint analysis.

For each issue:
1. Identify which distribution's guidelines apply
2. Verify the specific guideline cited
3. Check for accepted exceptions
4. Confirm the issue exists given the target distribution and RPM version
5. Verify rpmlint findings against actual packaging intent

Output:
- VERIFIED ISSUE: if the problem is real
- ELIMINATED: if the issue is a false positive
