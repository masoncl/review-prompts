# Distribution Detection and Guidelines Index

## Detection Logic

Determine the target distribution from these signals (in priority order):

1. **Explicit specification**: User states the target distribution
2. **%{dist} tag**: `.fc*` = Fedora, `.el*` = CentOS Stream / RHEL / EPEL
3. **Conditional macros**: `%{?fedora}`, `%{?rhel}`, `%{?centos}`
4. **Branch naming**: `f*`, `rawhide` = Fedora; `c*s` = CentOS Stream
5. **Mock/koji configuration**: references to Fedora or CentOS buildroots
6. **Default**: If unable to determine, assume Fedora (most strict guidelines)

## Distribution Guides

| Distribution | Triggers | File |
|--------------|----------|------|
| Fedora | .fc* dist, %{?fedora}, rawhide, f* branch | fedora.md |
| CentOS Stream | .el* dist, %{?rhel}, %{?centos}, c*s branch | centos-stream.md |

## Common Cross-Distribution Issues

### Macro Availability
Some macros exist only in certain distributions:
- `%forge*` macros - Fedora only (via forge-srpm-macros)
- `%pyproject_*` macros - Fedora; available in EPEL via pyproject-rpm-macros
- `%cargo_*` macros - Fedora primarily
- `%bcond` (without _with/_without) - newer RPM feature, check availability

### RPM Version Differences
- Fedora ships newer RPM with features like:
  - Boolean dependencies: `Requires: (pkgA or pkgB)`
  - Dynamic BuildRequires: `%generate_buildrequires`
  - `%conf` section (RPM 4.18+)
- CentOS Stream may not have these features depending on version
- See "Spec Feature Availability by RPM Version" in `spec-file.md` for
  RPM versions per release and how to check when a construct was added

### Weak Dependency Support
- Fully supported in Fedora
- Supported in EL8+ but used more conservatively
- `Recommends` and `Suggests` are most commonly used

### SPDX License Adoption
- Fedora: mandatory since F38
- CentOS Stream 10+: follows SPDX
- CentOS Stream 9: legacy license identifiers still common

### Compiler and Hardening Flags
- Both distributions set `%{optflags}` but values differ
- Fedora often has newer hardening defaults
- Spec files should never override these unless absolutely necessary
