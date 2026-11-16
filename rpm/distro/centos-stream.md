# CentOS Stream Packaging Guidelines

## When to Load

Load this file when the target distribution is CentOS Stream or RHEL
(detected by .el* dist tag, %{?rhel} or %{?centos} macros, or c*s branch
names).

## Relationship to Fedora Guidelines

CentOS Stream follows RHEL packaging practices, which derive from but
diverge from Fedora guidelines. Key principle: CentOS Stream is more
conservative than Fedora -- newer RPM features and macros may not be
available.

## Key Differences from Fedora

### RPM and Macro Version
- CentOS Stream ships older RPM than Fedora
- Some Fedora macros may not be available:
  - `%forge*` macros: may need `forge-srpm-macros` from EPEL
  - `%pyproject_*`: available in CentOS Stream 9+ but may differ from Fedora
  - `%bcond` shorthand: check RPM version
  - `%conf` section: RPM 4.18+, may not be in older EL versions
  - Dynamic `%generate_buildrequires`: check availability
  - Boolean dependencies: `(pkgA or pkgB)` syntax

### License Field
- CentOS Stream 10+: SPDX identifiers (following Fedora)
- CentOS Stream 9: legacy license identifiers still commonly used
- When in doubt, check what existing packages in the target use

### Compiler Flags and Hardening
- `%{optflags}` values differ from Fedora
- Hardening defaults may differ
- Spec files should respect distribution defaults

### Weak Dependencies
- Supported in EL8+
- Used more conservatively than in Fedora
- `Recommends` is the most commonly used weak dependency

### No %check Requirement
- Running tests is encouraged but not as strictly required as in Fedora
- Build environment may not have all test dependencies available

## EPEL Considerations

When packaging for EPEL (Extra Packages for Enterprise Linux):

### EPEL-Specific Guidelines
- Packages must not conflict with base RHEL/CentOS Stream packages
- Must not replace or update base packages
- Should use `epel-rpm-macros` for compatibility shims

### Conditional Macros for EPEL
```
# Available in EPEL packages
%{?epel}

# Target EL version
%{?rhel}

# Example: use different dependency on EPEL vs Fedora
%if 0%{?rhel}
Requires: python3-foo
%else
Requires: python3-foo >= 2.0
%endif
```

### Macro Compatibility
- `epel-rpm-macros` provides compatibility macros for features missing
  in base EL
- Check if `%pyproject_*` macros are available via EPEL packages

### EPEL 10 Minor Releases
EPEL 10 has a dist-git branch and repository per RHEL 10 minor version
(EPEL docs, `branches.adoc`):
- `epel10` builds for the leading minor version (dist tag `.el10_x` of
  the upcoming minor, against CentOS Stream 10). This is where version
  updates go
- `epel10.x` branches build for the trailing minor versions, against the
  matching RHEL 10.x. A trailing branch goes end-of-life once its minor
  version is no longer the leading release; Bodhi names them
  `EPEL-10.x`, so `EPEL-10.4` is not the same thing as fedrq's
  `-b epel10`
- Builds are tagged forward to newer minor versions automatically at
  mass branching, never backward (`build-tagging.adoc`)

What a trailing (`epel10.x`) branch takes:
- In general only security fixes, and only non-breaking ones
- Not version bumps, and not updates that need a breaking dependency
  update the trailing release does not have. Leave the branch at its
  current version instead of working around it; a package can stop
  being updatable in a trailing release (e.g. a Rust application whose
  new version needs a crate version only `epel10` has)
- Rust `-devel` (library-only) packages have a blanket update exception
  in Fedora stable releases (FESCo Updates Policy, "Rust -devel
  packages"). The EPEL Steering Committee granted them a permanent
  exception in the leading branches only, `epel9` and `epel10`
  (https://forge.fedoraproject.org/epel/steering/issues/316, meeting of
  2025-02-26; not yet in the EPEL docs). There is no exception for
  trailing `epel10.x` branches, so crates there are not updated; an
  update that needs one requires its own Steering Committee ticket
- A breaking (incompatible) update, typically a security fix that
  cannot be backported, needs the EPEL incompatible upgrades process
  (`epel-policy-incompatible-upgrades.adoc`,
  https://docs.fedoraproject.org/en-US/epel/epel-policy-incompatible-upgrades/):
  epel-devel thread and Bugzilla bug, an EPEL Steering Committee issue
  approved at a weekly meeting, epel-announce mails when submitting and
  when pushing stable, at least a week in testing without autopush. This
  applies to incompatible upgrades in any EPEL branch, `epel10`
  included; non-security incompatible updates are not allowed at all
  (ship a parallel package such as `foo2` instead)

## RHEL Jira Issues for CentOS Stream Contributions

- File one issue per CentOS Stream branch, with that branch's
  `CentOS Stream N` as the only Affects Version, and let Red Hat set the
  RHEL versions and z-streams. Jira accepts several values, but the RHEL
  project has a single-value policy for the field: a sync bot
  ("GitLab Component Sync") strips extra values, saying it keeps the
  first one listed. On RHEL-123605 (2026-10-01) it removed three of
  four extras and left `rhel-10.0`, so what survives is unpredictable
- Resolution "Done" does not mean a fix shipped: issues get closed
  straight from New, with no Fix Version, while their merge requests
  are still open (RHEL-123605, RHEL-123606). Before treating an issue
  as fixed, check that the merge request was merged or that the change
  is in the released package

## Merge Requests in CentOS Stream Dist-git

- Stream dist-git projects on GitLab merge by fast-forward without
  squashing (`merge_method` `ff`, `squash_option` `never` on
  redhat/centos-stream/rpms bash, blktrace, git, glibc, python3.12
  and systemd, checked 2026-11-16), so every commit in an MR lands in
  the package's history as written. A fix-up commit ("Set Release to
  match the changelog") stays there for good, with a second
  `Resolves: RHEL-...` line
- To fix a commit in an open MR, amend it and push the source branch
  with `--force-with-lease`. Check the project's settings first,
  since others may differ:
  `glab api projects/<url-encoded path> | jq .merge_method,.squash_option`
- If a SIG branch carries the same commit and a CBS build was made
  from it, push a tag at the old commit to the SIG repo before
  force-pushing, so the build's source stays reachable

## Build System Differences

### CentOS Stream Build Pipeline
- Uses different build infrastructure than Fedora (Brew/MBS vs Koji)
- Module builds may be relevant for some packages
- Side tags and build dependencies may work differently

### Mock Configuration
- Use the appropriate mock config for the target:
  - `centos-stream-9-x86_64`
  - `centos-stream-10-x86_64`
- Don't assume Fedora mock configs work for CentOS Stream

## Common CentOS Stream Issues

1. **Using Fedora-only macros** without checking availability
2. **SPDX identifiers** on older CentOS Stream (use legacy format)
3. **Boolean dependencies** not supported in older RPM versions
4. **Missing EPEL dependencies** when backporting Fedora packages
5. **Different Python version** than Fedora (especially on older EL)
