---
name: rpm-review
description: Review RPM spec files and packages for policy compliance and issues
---

Using the prompt {{REVIEW_DIR}}/review-core.md, run a systematic review of
the specified spec file or package.

If no specific file is specified, look for *.spec files in the current
directory.

Load {{REVIEW_DIR}}/technical-patterns.md first, then follow the complete
review protocol in review-core.md.

For the spec file or package being reviewed:
1. Detect the target distribution
2. Load distribution-specific guidelines
3. Review against the complete checklist
4. Classify findings by severity
5. Create report if issues found
