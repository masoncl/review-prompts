# RPM Package Review Protocol

## Overview

This protocol guides systematic review of RPM packages -- both spec files
and built packages -- for correctness, policy compliance, and potential issues.

## Pre-Review Setup

Before beginning review:
1. ALWAYS load `technical-patterns.md` first
2. Load `distro/distro.md` and detect the target distribution
3. Load distribution-specific files based on detected context (see triggers below)
4. Load `ecosystem/ecosystem.md` and any matching language ecosystem files
5. Load additional files based on review content (see conditional loading)

## TASK 0: Context Detection

Detect the review context:
- Is this a spec file review, a built package review, or both?
- Determine target distribution from:
  - %{dist} tag value (.fc*, .el*)
  - Macro usage patterns (%{fedora}, %{rhel}, %{centos})
  - Repository structure (if in dist-git: Fedora vs CentOS Stream branch naming)
  - BuildRoot or mock configuration references
  - Presence of fedora-review or rpmlint configuration
- Load the matching distribution file from distro/

## TASK 1: Distribution Context Loading

Load distribution files based on detected context:

| Trigger | File to Load |
|---------|--------------|
| .fc* dist tag, %{fedora} macro, Fedora branch names | `distro/fedora.md` |
| .el* dist tag, %{rhel}/%{centos} macro, c*s branches | `distro/centos-stream.md` |
| Spec file present | `spec-file.md` |
| Custom or complex macro definitions | `macros.md` |
| %pre, %post, %preun, %postun, %pretrans, %posttrans | `scriptlets.md` |
| BuildRequires, Requires, Provides, Conflicts, Obsoletes | `dependencies.md` |
| License:, %license, SPDX | `licensing.md` |
| CVE bugs, advisories, `Provides: bundled(...)` copies | `security.md` |
| %cargo_*, %gometa/%gobuild, %pyproject_*/%py3_* (see index) | `ecosystem/ecosystem.md` + matching file |

## TASK 2: Spec File Review Checklist

Only when reviewing spec files.

### 2.1 Header Section
- [ ] Name follows naming conventions for target distro
- [ ] Version/Release format correct (%{?dist} present in Release)
- [ ] Source/Source0 uses proper URL with %{version} macro
- [ ] License field uses correct format (SPDX for Fedora 38+)
- [ ] URL is valid and points to upstream project
- [ ] BuildRequires are complete and minimal
- [ ] ExclusiveArch/ExcludeArch used only when necessary

### 2.2 %prep Section
- [ ] %setup/%autosetup used correctly
- [ ] Patches applied in correct order
- [ ] Patch application method matches patch format

### 2.3 %build Section
- [ ] Build system macros used (%cmake, %meson, %configure, %make_build)
- [ ] Compiler flags not overridden (respect distribution defaults)
- [ ] Parallel build enabled (%make_build or equivalent)

### 2.4 %check Section
- [ ] Test suite run when available
- [ ] Test failures not silently ignored

### 2.5 %install Section
- [ ] Uses %{buildroot} consistently
- [ ] Installs to correct FHS-compliant directories via macros
- [ ] %find_lang used for locale files
- [ ] Desktop files validated if present

### 2.6 %files Section
- [ ] All installed files owned by a package
- [ ] No duplicate file ownership between subpackages
- [ ] Correct use of %doc, %license, %config, %ghost, %dir
  - %license only required in subpackages that can be installed independently
    of any other subpackage that ships the license file
- [ ] No ownership of system directories (%{_bindir}, etc.)
- [ ] %{_isa}-qualified dependencies where needed

### 2.7 %changelog Section
- [ ] Format correct: * Day-of-week Mon DD YYYY Name <email> - Version-Release
- [ ] Most recent entry first
- [ ] Entries describe actual changes

## TASK 3: Built Package Review Checklist

Only when reviewing built RPMs.

### 3.1 rpmlint Analysis
- [ ] Interpret rpmlint warnings and errors
- [ ] Distinguish real issues from false positives
- [ ] Check for common rpmlint patterns that indicate real problems

### 3.2 File Permissions and Ownership
- [ ] No world-writable files (except where intentional)
- [ ] SUID/SGID binaries justified
- [ ] Config files marked as %config(noreplace) where appropriate
- [ ] Correct ownership for service files and directories

### 3.3 Scriptlet Safety
- [ ] Scriptlets handle fresh install vs upgrade correctly ($1 checks)
- [ ] Scriptlets do not fail on uninstall
- [ ] systemd macro usage for services (%systemd_post, etc.)
- [ ] No interactive prompts in scriptlets

### 3.4 Dependency Correctness
- [ ] Automatic dependency generation not accidentally disabled
- [ ] No unnecessary explicit Requires on auto-detected dependencies
- [ ] Correct use of virtual Provides
- [ ] Proper Obsoletes/Conflicts for package renames/splits

## TASK 4: Verification

Goal: Eliminate false positives.

1. If NO issues found: report clean review, proceed to Task 5
2. If issues found:
   - Load `false-positive-guide.md`
   - Apply each verification check
   - Apply the "False Positives" section of any loaded ecosystem file
   - Remove any false positives from findings
3. When uncertain whether a pattern is correct, consult real-world examples:
   - For Fedora: download and search the spec archive at
     https://src.fedoraproject.org/lookaside/rpm-specs-latest.tar.xz
     to verify whether the flagged pattern is common practice

## TASK 5: Reporting

The report supports a human reviewer; it is not an approval or rejection.
Do not state that a package is approved or that the review flag should be
set. For Fedora, follow the "AI-Assisted Contributions" section of
`distro/fedora.md` when the report is posted (disclose AI assistance).

Structure findings by severity:

**CRITICAL**: Security issues, broken dependencies, data loss potential
- World-writable files with sensitive content
- Missing dependencies causing runtime failures
- Scriptlets that can destroy data

**HIGH**: Policy violations, functional problems
- Incorrect License field
- Missing or wrong BuildRequires
- Broken scriptlets
- Files installed in wrong locations

**MEDIUM**: Best practice violations, potential issues
- Deprecated macro usage
- Missing %{?_isa} on arch-specific dependencies
- Suboptimal spec file structure

**LOW**: Cosmetic, suggestions
- Changelog formatting
- Minor macro style preferences
- Spec file organization

For each issue report:
1. Location (spec file section/line or package file path)
2. Severity level
3. Description of the issue
4. Suggested fix
5. Reference to packaging guidelines (if applicable)
