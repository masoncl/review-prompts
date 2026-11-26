# RPM Review False Positive Elimination Guide

## Purpose

This guide helps eliminate false positives before reporting packaging issues.
Apply these checks to every potential issue found.

## Core Principle

**Never report a packaging issue you cannot justify with concrete evidence
from the spec file, built package, or applicable packaging guidelines.**

## Verification Checks

### CHECK 1: Is This a Real Policy Violation?

Before reporting a guidelines violation:
1. Verify which distribution's guidelines apply
2. Find the specific guideline section that is violated
3. Confirm the guideline has not been superseded or relaxed

**False Positive Example**: Flagging lack of %check section when the
upstream project has no test suite.

### CHECK 2: Is This Distribution-Specific?

Many "rules" apply only to certain distributions:
- Fedora requires SPDX license identifiers (F38+); CentOS Stream may accept legacy
- Fedora weak dependency usage differs from RHEL
- Macro availability varies between RPM versions across distros
- %forge macros are Fedora-specific

**Check**: Verify the rule applies to the detected target distribution.

### CHECK 3: Is This an Acceptable Exception?

Some packages legitimately diverge from guidelines:
- Compatibility packages may need non-standard naming
- Compat libraries may ship static archives
- Language-specific packages follow language-specific guidelines
  (Python, Rust, Go, Ruby, etc.); see the "False Positives" section of the
  matching `ecosystem/*.md` file
- Bootstrapping packages may have circular dependency workarounds

### CHECK 4: Is the Macro Actually Wrong?

Macro usage evolves across RPM and distribution versions:
- %{buildroot} vs $RPM_BUILD_ROOT (both valid, style preference varies)
- %make_build is newer; %{?_smp_mflags} still works
- %license was not always available; %doc for license files was previously correct
- %autosetup vs %setup -q (both valid depending on patch handling needs)

**Do not flag deprecated-but-still-functional macros as errors -- flag as LOW
suggestions only.**

### CHECK 5: Is rpmlint Correct Here?

rpmlint produces false positives regularly:
- `spelling-error` on legitimate technical terms
- `no-manual-page-for-binary` when man page is in a separate -doc subpackage
- `non-standard-dir-perm` for intentional directory permissions
- `dangling-symlink` for symlinks resolved at install time
- `no-documentation` for minimal utility packages

**Check**: Verify rpmlint finding against actual packaging intent.

#### rpmlintrc Filters

A confirmed false positive is documented with a filter in
`<name>.rpmlintrc` at the dist-git root, which `fedpkg lint` passes to
rpmlint with `-r` and `fedpkg import` keeps (rpmlint 2.8.0, rpkg 1.70):
- Narrow each filter to the finding. Messages read
  `<name>.<arch>: <E|W>: <check> <args>`, so
  `addFilter(r"foo\.noarch: E: spelling-error \('nonfree', ")` hides only
  that word in that subpackage, and a new typo still reports. Anchor
  with `$` where the argument ends the line
- A filter that matched nothing is reported as
  `E: unused-rpmlintrc-filter "<regex>"`. The check runs once, after the
  last package of the invocation, against the filters used anywhere in
  it. Lint the spec, SRPM and all binary RPMs in one run: linting the
  spec alone, or the RPMs in separate runs, turns every filter for the
  other packages' findings into an error. Don't ask for such filters to
  be removed on the strength of a partial run
  - `--ignore-unused-rpmlintrc` turns the check off, and with it the
    detection of stale filters. A filter for `unused-rpmlintrc-filter`
    itself has no effect: rpmlint never filters that message
- Without `-r`, rpmlint loads a `*.rpmlintrc` or `*-rpmlintrc` only when
  given exactly one path, from that file's directory (or that
  directory). With several paths (spec plus RPMs) nothing is loaded, so
  pass `-r`. If more than one file matches, all are ignored with a
  warning
- `-r` takes a single file, so one run cannot combine a spec/SRPM
  rpmlintrc with one for the binary RPMs. Splitting the filters by
  package type means separate runs, each given only the packages its
  file applies to
- `fedpkg lint` lints the spec plus the RPMs in the checkout: the
  `fedpkg mockbuild` results (`results_<name>/<version>/<release>/`) if
  present, otherwise the SRPM and `<arch>/` directories `fedpkg local`
  leaves, without -debuginfo and -debugsource. Results built elsewhere
  are not seen, so binary-RPM filters show up as unused; run
  `rpmlint -r <name>.rpmlintrc <name>.spec <resultdir>/*.rpm` instead

### CHECK 6: Is This a Subpackage Split Decision?

Subpackage organization is often a judgment call:
- -devel, -libs, -doc splits may vary by project size
- Not every project needs a -libs subpackage
- Single-binary packages may not need subpackages at all

**Do not flag**: Missing subpackage splits unless policy mandates them.

### CHECK 7: Changelog and Cosmetic Issues

- Changelog format varies slightly between tools that generate it
- Date format has acceptable variations
- Changelog completeness is subjective

### CHECK 8: Conditional Content

Spec files often have conditional sections:
- `%if 0%{?fedora}` blocks are intentionally distro-specific
- `%bcond` toggles are intentional build configuration
- Architecture conditionals reflect real platform differences

**Do not flag**: Conditional blocks as "dead code" unless provably unreachable
on ALL supported configurations.

## Elimination Process

For each potential issue:

1. [ ] Can I cite the specific guideline or standard violated?
2. [ ] Does this guideline apply to the target distribution?
3. [ ] Is this not an accepted exception for this type of package?
4. [ ] Is the current approach actually wrong (not just non-preferred)?
5. [ ] Would a package reviewer flag this in a real review?

**If any answer is NO or UNCERTAIN**, do not report the issue.

## Common False Positives Summary

1. **Missing %check** -- not all packages have test suites
2. **%define vs %global** -- %define is not wrong, just less preferred
3. **rpmlint spelling-error** -- often legitimate technical terms
4. **Missing man pages** -- may be in -doc subpackage or an upstream issue
5. **Group tag missing** -- Group is ignored in modern RPM
6. **Missing BuildRoot** -- not needed in modern RPM (RHEL 7+)
7. **%clean section missing** -- not needed in modern RPM
8. **ExclusiveArch missing** -- only needed when package truly cannot build elsewhere
9. **Bundled library** -- may be justified if system version is incompatible
10. **Static library in main package** -- only wrong if -static subpackage policy applies
11. **Missing %license in subpackage** -- not needed if the subpackage has a hard
    Requires on another subpackage that ships the license file (e.g., -devel
    requires -libs which includes %license)

## When Uncertain

If unsure whether something is a violation:
1. Check if the same pattern exists in other packages for the target distro
2. Look for the specific guideline that would be violated
3. Consider if flagging would actually improve the package
4. When in doubt, don't flag -- ask for clarification instead
