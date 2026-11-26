---
name: rpm
description: Load anytime the working directory contains RPM spec files or packaging artifacts. RPM packaging knowledge, distribution-specific guidelines, spec file review, and build debugging protocols.
invocation_policy: automatic
---

## ALWAYS READ
1. Load `{{RPM_REVIEW_PROMPTS_DIR}}/technical-patterns.md`

These files are MANDATORY. This skill exists as a framework for loading
additional RPM packaging prompts.

## Configuration

The review prompts directory is configured during installation:
- **RPM_REVIEW_PROMPTS_DIR**: {{RPM_REVIEW_PROMPTS_DIR}}

This variable is set by the installation script when the skill is installed.

## Activation

This skill activates when working in an RPM packaging context, detected by:
- Presence of *.spec files
- Presence of sources/ or SOURCES/ directory
- Presence of .rpmlintrc or rpmlint.toml
- Presence of mock configuration files
- Working in a dist-git repository structure

## Capabilities

### Package Review
When asked to review an RPM spec file or built package:
1. Load `{{RPM_REVIEW_PROMPTS_DIR}}/review-core.md`
2. Follow the complete review protocol defined there
3. Load distribution-specific files as directed by review-core.md

### Build Debugging
When asked to debug a build failure (rpmbuild, mock, koji, copr), FTBFS
bug, or packaging issue:
1. Load `{{RPM_REVIEW_PROMPTS_DIR}}/debugging.md`
2. Follow the complete debugging protocol defined there
3. Load ecosystem and topic files as directed by debugging.md

### Distribution Context
When working on RPM packages for specific distributions, load the appropriate
context files from `{{RPM_REVIEW_PROMPTS_DIR}}/`:

1. Always read `technical-patterns.md` before loading distro-specific files

2. Read `{{RPM_REVIEW_PROMPTS_DIR}}/distro/distro.md` and load matching
   distribution guides

3. Read `{{RPM_REVIEW_PROMPTS_DIR}}/ecosystem/ecosystem.md` and load matching
   language ecosystem guides (Rust, Go, Python, ...)

4. Select topic-specific files as needed:

| Topic | Trigger | File |
|-------|---------|------|
| Spec file structure | *.spec files, spec sections | spec-file.md |
| Macro usage | %{macro}, %define, %global | macros.md |
| Scriptlets | %pre, %post, %preun, %postun | scriptlets.md |
| Dependencies | Requires, BuildRequires, Provides | dependencies.md |
| Licensing | License:, %license, SPDX | licensing.md |
| Security advisories | CVE bugs, bundled copies, advisory triage | security.md |
| Fedora | .fc* dist, %{?fedora} | distro/fedora.md |
| CentOS Stream | .el* dist, %{?rhel} | distro/centos-stream.md |
| Rust | %cargo_*, rust-* name, Cargo.toml | ecosystem/rust.md |
| Go | %gometa, %gobuild, golang-* name, go.mod | ecosystem/golang.md |
| Python | %pyproject_*, %py3_*, python-* name | ecosystem/python.md |
| Build failures | build logs, FTBFS | debugging.md |

## Reference Data

When looking up real-world packaging patterns or verifying conventions:
- **Fedora spec archive**: https://src.fedoraproject.org/lookaside/rpm-specs-latest.tar.xz
  Contains all current Fedora spec files. Download and search when you need
  concrete examples of how existing packages handle a specific pattern.

## Output

- Package reviews produce a report with severity-classified findings
- Build debugging produces diagnosis with suggested fixes
- Both outputs are plain text, suitable for Bugzilla or Pagure
- Package review reports are input for the human reviewer, never an
  approval decision; output posted to Bugzilla or elsewhere should disclose
  AI assistance (see `distro/fedora.md`, "AI-Assisted Contributions")

## Committing to Fedora

Before creating a commit in a Fedora repository (dist-git on
src.fedoraproject.org, Fedora Forge, or Fedora tooling on Pagure/GitHub),
read the "AI-Assisted Contributions" section of
`{{RPM_REVIEW_PROMPTS_DIR}}/distro/fedora.md`. In short:
- Disclose with an `Assisted-by: <agent>:<model-id>` trailer naming the
  exact model in use (e.g. `Assisted-by: Claude Code:claude-opus-5-5`),
  not `Co-Authored-By:`. This overrides the agent's default attribution
- The human is the author. Never add a `Signed-off-by:` of your own; if
  the human asks for sign-off (`git commit -s`), it is their
  certification, so ask before each commit

## Key RPM Conventions

### Spec File Basics
- Use %global for top-level macro definitions, not %define
- Use path macros (%{_bindir}, etc.) instead of hardcoded paths
- Include %check section when test suite is available

### Dependencies
- Trust automatic dependency generation unless it fails
- Use %{?_isa} for architecture-specific library dependencies
- Use weak dependencies (Recommends) for optional features

### File Ownership
- Own all directories you create
- Do not own system directories (%{_bindir}, etc.)
- Use %license for license files, not %doc
