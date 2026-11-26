---
name: rpm-debug
description: Debug RPM build failures and packaging issues
---

Using the prompt {{REVIEW_DIR}}/debugging.md, analyze the provided build log,
error message, or packaging issue.

Load {{REVIEW_DIR}}/technical-patterns.md first, then follow the complete
debugging protocol in debugging.md, loading ecosystem and topic files as
it directs.

Expected input:
- rpmbuild output/error messages
- mock build logs (root.log, build.log, state.log)
- koji/copr task IDs, URLs, or build failure logs
- FTBFS bug reports
- rpmlint output
- Dependency resolution or install-time errors

The protocol will:
1. Identify the failure type and the first relevant error (spec parse,
   buildroot/dependency resolution, %prep/%build/%check/%install,
   %files/unpackaged files, post-install checks and debuginfo,
   rpmlint, install-time dependency or scriptlet errors)
2. Locate and read the relevant logs
3. Reproduce where possible (mock, fedpkg mockbuild)
4. Determine whether the cause is the spec, upstream, or a buildroot change
5. Suggest a minimal fix with concrete spec file changes
