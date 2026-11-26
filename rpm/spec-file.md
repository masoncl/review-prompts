# Spec File Deep Dive

## When to Load

Load this file when reviewing or working with RPM spec files directly.

## Canonical Section Ordering

1. **Header** - Name, Version, Release, Summary, License, URL, Source, Patch,
   BuildRequires, Requires, and other metadata tags
2. **%description** - Package description (can be multi-line)
3. **%package** subpackages - Each with its own Summary, Requires, %description
4. **%prep** - Source unpacking and patch application
5. **%build** - Compilation
6. **%check** - Test suite execution
7. **%install** - Installation to buildroot
8. **%files** - File listing for main package and each subpackage
9. **%changelog** - Change history

## Header Field Reference

### Required Fields
- `Name:` - package name (lowercase, hyphens OK, no underscores)
- `Version:` - upstream version
- `Release:` - package release, must include `%{?dist}`
- `Summary:` - one-line description (no trailing period)
- `License:` - SPDX expression (Fedora 38+) or legacy tag
- `URL:` - upstream project URL
- `Source0:` - source tarball URL (use `%{version}` macro)

### Common Optional Fields
- `BuildArch: noarch` - for architecture-independent packages
- `ExclusiveArch:` - limit to specific architectures
- `Epoch:` - version epoch (avoid if possible)
- `BuildRoot:` - not needed in modern RPM

## Name-Version-Release Conventions

### Standard Release
```
Release: 1%{?dist}
```

### Snapshot/Pre-release Versioning
```
# For pre-release snapshots (0.x release so it sorts before 1)
%global commit abc123def456
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapdate 20240101

Version: 1.2.0
Release: 0.1.%{snapdate}git%{shortcommit}%{?dist}
```

### Pre-release Versions (alpha, beta, rc)
```
Version: 1.2.0
Release: 0.1.rc1%{?dist}
```

### Epoch
- Avoid epoch if at all possible
- Only use when upstream changes versioning scheme in a way that breaks
  RPM version comparison
- Once set, epoch can never be removed

## Source and Patch Management

### Source URL Best Practices
```
# Use macros for version in URL
Source0: https://example.com/releases/%{name}-%{version}.tar.gz

# GitHub sources
Source0: https://github.com/owner/repo/archive/v%{version}/%{name}-%{version}.tar.gz

# Forge macros (Fedora)
%forgemeta
Source0: %{forgesource}
```

### Patch Handling
```
# Named patches
Patch0: fix-build.patch
Patch1: add-feature.patch

# In %prep with %autosetup (applies all patches automatically)
%autosetup -p1

# Or manually
%setup -q
%patch 0 -p1
%patch 1 -p1
```

### Patches That Apply Only Sometimes
Declare every `PatchN:` unconditionally and make only applying it
conditional. A `Patch:` inside `%if` or `%ifarch` is missing from an
SRPM built where the condition is false: the Fedora guidelines forbid
architecture-conditional `Source:` and `Patch:` tags for this reason,
and release conditions fail the same way (Hyperscale's rasdaemon,
2026-11-18: an EL9-only patch under `%if 0%{?rhel} < 10` was missing
from an SRPM built on a Fedora host by a tool that didn't define
`%rhel`).

One way to keep this readable is to number patches by audience,
lower numbers applying more widely, and apply each block with
`%autopatch -m`/`-M`. Since rpm 4.15 an unnumbered `Source:` or
`Patch:` takes the previous number plus one (the first is 0), so only
the reserved blocks need numbers:
```
Source:   %{name}-%{version}.tar.gz
Patch:    rasdaemon-1.0.0-unified-sel-any-arch.patch   # everyone
Patch200: rasdaemon-1.0.0-python3.9.patch              # EL9 only

%prep
%autosetup -N
%autopatch -p1 -M 99
%if 0%{?rhel} && 0%{?rhel} < 10
%autopatch -p1 -m 200 -M 299
%endif
```
- Pick the blocks per package: patches for everyone first (up to 99,
  199 or 999), then blocks for an architecture, a release, and so on.
  In CentOS Hyperscale the highest block is normally for the
  Facebook-only builds
- Keep the unnumbered patches before the first numbered one: an
  unnumbered `Patch:` after `Patch200:` becomes 201 and joins that
  block
- Automatic numbering and `%autopatch -m`/`-M` need rpm 4.15 or later
  (EL9 and newer, current Fedora). On EL8 number every patch and
  apply the conditional ones with `%patch -P <n> -p1`
- In review, a conditionally declared `Patch:` is a finding: a
  MUST NOT for architecture conditions, and the same failure for
  release conditions

### Patch Provenance
When reusing patches from another packager's COPR, SRPM or another
distribution, check where each patch came from before carrying it:
the patch header (`From:`, `Subject:`, `X-Git-Url:`), comments next to
the `Patch:` line, and the upstream tracker. A patch found in someone's
COPR is often an upstream commit by a different author, or that
packager's own upstream commit adapted to an older release.
- Credit the real author: the patch file keeps its upstream `From:`;
  the packager who carries it authors the dist-git commit
- Link the upstream commit, merge request or bug in a comment above the
  `Patch:` line, not just the COPR or distribution it was found in
- Say "backport of" when the patch was adapted to the packaged release
  (reformatted, rebased, autotools or build-system changes)
```
# Backport of upstream commit 1a2b3c4 (merged in 2.4.0), adapted to 2.3
# https://gitlab.example.org/project/-/commit/1a2b3c4
Patch0: project-2.3-fix-foo.patch
```

### Backporting Upstream Commits
Carry each upstream commit as its own patch, in `git format-patch` form,
from a URL that `spectool -g` can download, rather than one
hand-combined diff. This keeps upstream's authorship and commit
messages, and a reviewer can check each patch by fetching it and
comparing (`spectool -g`, `cmp`). Name the local file after what the
patch does with a `#/` suffix (the URL already has the hash), and commit
the downloaded file under that name:
```
# GitHub (GitLab: <project-url>/-/commit/<sha>.patch)
Patch:  %{url}/commit/<sha>.patch#/%{name}-fix-foo.patch
# gitweb: a=patch serves format-patch output
Patch:  https://<host>/?p=<repo>.git;a=patch;h=<sha>#/%{name}-fix-foo.patch
```
- Apply them in upstream order. When upstream needed several attempts,
  skip pairs that cancel out (a commit and its revert; check that
  `git diff <commit>^ <revert>` is empty) and say so in the comment
- If a patch needs light edits to apply to the packaged release (e.g. a
  `NEWS`/`CHANGELOG` hunk that conflicts), carry it as a local file
  instead, with the upstream URL in the comment and what was edited
- Look for the fix upstream and credit its author first (see
  `debugging.md`, Sending the Fix Upstream)

Example (claws-mail 4.4.0, libical 4 support):
```
# vCalendar plugin: build with libical 4 (claws-mail bug 4942), and keep
# building with libical 3; upstream commits, in order (two reverted
# attempts in between cancel out)
Patch12: https://git.claws-mail.org/?p=claws.git;a=patch;h=1ad8482186cdcd056047aa5f9e2d495e6296a1bb#/claws-mail-vcalendar-libical4.patch
Patch13: https://git.claws-mail.org/?p=claws.git;a=patch;h=f754d8d9ae50f2beb1385798c541af623d5c2820#/claws-mail-vcalendar-libical3-compat.patch
Patch14: https://git.claws-mail.org/?p=claws.git;a=patch;h=9b6b82879c75ceb52d93eaa137eafe04b258136e#/claws-mail-vcalendar-libical4-version-check.patch
```

## Subpackage Organization

### Common Subpackage Patterns

```
# Development files
%package devel
Summary: Development files for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}

# Shared libraries (when main package has binaries too)
%package libs
Summary: Shared libraries for %{name}

# Documentation
%package doc
Summary: Documentation for %{name}
BuildArch: noarch
```

### When to Split
- `-devel` - when package ships headers and/or pkgconfig files
- `-libs` - when main package has binaries and also ships shared libraries
- `-doc` - for large documentation sets (reduces base install size)
- `-static` - for static library archives (not shipped by default)
- Language bindings - `-python3`, `-perl`, etc.

## Architecture Handling

### noarch Packages
- Pure data, scripts, or interpreted language modules
- Set `BuildArch: noarch` in the header

### Architecture-Specific Dependencies
```
# Use %{?_isa} for library dependencies
Requires: libfoo%{?_isa} >= 1.2

# But NOT for -devel packages requiring their own -libs
# (already implied by the build)
```

### Conditional Architecture Blocks
```
%ifarch x86_64
# x86_64-specific configuration
%endif

%ifnarch s390x
# everything except s390x
%endif
```

## Spec Feature Availability by RPM Version

Before using a newer spec construct on older branches (EPEL, CentOS
Stream), check which RPM version introduced it and which RPM version the
target release ships.

### RPM Version per Release

Checked 2026-11-02 with `fedrq pkgs -b <branch> -F nevra rpm`:

| Branch | RPM |
|--------|-----|
| EL8 (`al8`, AlmaLinux) | 4.14.3 |
| c9s | 4.16.1.3 |
| c10s | 4.19.1.1 |
| f44 | 6.0.2 |
| f45 | 6.1.0 |
| rawhide | 6.1.0 |

`c8s` and `c7` return nothing because they are EOL and their mirrors are
gone. EL7 (RPM 4.11) and EL6 (RPM 4.8) are unverified, and both releases
are EOL. Re-check with `fedrq` when it matters, since these move.

### Constructs and the RPM Version That Introduced Them

| Construct | Introduced | Notes |
|-----------|------------|-------|
| `OrderWithRequires:` | 4.9.0 | Upstream commit 5c43095e1 (2010-12-13, "Implement transaction ordering hinting"); absent in rpm-4.8.1-release. Parsed like `Requires:`, so it takes the same qualifiers (`(post)` etc.); `%{?systemd_ordering}` relies on this |

### Finding When a Construct Was Introduced

Use rpm's git history:
```
git log -S'<keyword>' --reverse          # first commit mentioning it
git tag --contains <commit>              # first release containing it
git grep -i '<keyword>' rpm-X.Y.Z-release -- build/   # present in a release?
```
Upstream docs and the manual give the version for some constructs, but
not all.
