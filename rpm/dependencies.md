# RPM Dependency Management

## When to Load

Load this file when reviewing BuildRequires, Requires, Provides, Conflicts,
Obsoletes, weak dependencies, or dependency generation issues.

## Dependency Types

### Build-Time
- `BuildRequires:` - packages needed to build (installed in build chroot)

### Runtime (Strong)
- `Requires:` - mandatory runtime dependencies
- `Requires(pre):` - needed before %pre scriptlet
- `Requires(post):` - needed before %post scriptlet
- `Requires(preun):` - needed before %preun scriptlet
- `Requires(postun):` - needed before %postun scriptlet

### Runtime (Weak)
- `Recommends:` - installed by default, can be removed
- `Suggests:` - not installed by default, shown as suggestion
- `Supplements:` - inverse of Recommends (if X is installed, also install this)
- `Enhances:` - inverse of Suggests

### Relationship
- `Provides:` - capabilities this package provides
- `Conflicts:` - cannot be installed alongside these packages
- `Obsoletes:` - replaces these packages (triggers auto-removal)

## Automatic Dependency Generation

RPM automatically detects dependencies by scanning installed files:

### What Auto-Deps Detect
- **ELF binaries**: shared library linkage (Requires: libfoo.so.1()(64bit))
- **Python**: imports in .py files
- **Perl**: use/require statements
- **pkgconfig**: .pc file Requires
- **Ruby gems**: gemspec dependencies

### When Auto-Deps Fail
- Private shared libraries (not in standard library paths)
- dlopen() loaded libraries
- Scripting language plugins loaded at runtime
- Cross-language dependencies (C library used via FFI)

### Filtering Auto-Dependencies
```
# Filter out private library from auto-requires
%global __requires_exclude ^libprivate\\.so

# Filter out private library from auto-provides
%global __provides_exclude ^libprivate\\.so

# Filter Python auto-requires
%global __requires_exclude ^python3dist\\(private-module\\)
```

## Architecture-Qualified Dependencies

### When to Use %{?_isa}
```
# Library dependencies between subpackages
Requires: %{name}-libs%{?_isa} = %{version}-%{release}

# Dependencies on other architecture-specific libraries
Requires: libfoo%{?_isa} >= 1.2
```

### When NOT to Use %{?_isa}
```
# noarch packages
Requires: python3-foo

# Packages that are always noarch
Requires: bash

# -devel requiring its own -libs (already arch-matched by build)
# Still use it for clarity, but it's technically redundant
```

## Weak Dependencies

### Recommends (installed by default, removable)
```
# Plugin that most users want but is optional
Recommends: %{name}-plugin-common
```

### Suggests (not installed by default)
```
# Completely optional enhancement
Suggests: %{name}-extras
```

### Supplements/Enhances (inverse direction)
```
# If user has package X, also install this
Supplements: (packageX and %{name})
```

### Distribution Policy
- Fedora: weak dependencies widely supported and encouraged
- CentOS Stream / RHEL: supported in EL8+, use conservatively

## Obsoletes/Conflicts for Package Transitions

### Package Rename
```
# New package replaces old one
Provides: oldname = %{version}-%{release}
Obsoletes: oldname < %{version}-%{release}
```

### Package Split
```
# Main package split into -libs and -tools
# In -libs:
Obsoletes: %{name} < 2.0-1
# (only the version where the split happened)

# In -tools:
Obsoletes: %{name} < 2.0-1
```

### Version-Bounded Obsoletes
```
# CORRECT - always version-bound Obsoletes
Obsoletes: oldpkg < 1.5.0-3

# WRONG - unbounded Obsoletes prevents oldpkg from ever returning
Obsoletes: oldpkg
```

## Dependency Debugging

### Inspect Package Dependencies
```
# Show requires of a built RPM
rpm -qp --requires package.rpm

# Show provides of a built RPM
rpm -qp --provides package.rpm

# Find what requires a given capability
dnf repoquery --whatrequires 'libfoo.so.1()(64bit)'

# Find what provides a given capability
dnf repoquery --whatprovides 'pkgconfig(foo)'
```

### Query Other Releases and Distributions With fedrq
`fedrq` queries Fedora, EPEL, CentOS Stream, AlmaLinux, Rocky, Oracle
Linux, UBI, Amazon Linux and ELN without any local repository
configuration:
```
fedrq pkgs -b <branch> -F nevra <pkg>    # package version on a branch
fedrq whatrequires -b <branch> <pkg>     # reverse dependencies (binary)
fedrq wrsrc -b <branch> <pkg>            # reverse dependencies (source
                                         # packages), e.g. for mass rebuilds
fedrq subpkgs -b <branch> <srpm-name>    # binary packages of a source package
fedrq download-spec -b <branch> <srpm-name>
fedrq pkgs -r @baseurl:file://<dir> '*' # a local repository, e.g. mock
                                         # results with repodata
```
- Branch names: `rawhide`, `fNN`, `epelN`, `epelN-next`, `cNs`, `alN`,
  `rlN`, `olN`, `ubiN`, `amazonN`, `eln`
- `epelN` queries only the EPEL repositories; for base OS packages use
  `cNs` or `alN`/`rlN`
- EOL branches (e.g. `c8s`, `c7`) can return nothing
- Tested with fedrq 1.7.0

#### fedrq Pitfalls
Most of these fail silently: a wrong subcommand, flag or formatter
inside a pipeline with `2>/dev/null` looks like a legitimate empty
answer. Sanity-check the count at each stage of a pipeline.

Queries and formatters:
- There is no `whatprovides` subcommand
  (https://forge.fedoraproject.org/packaging/fedrq/issues/119). Resolve a
  capability to its providers with `fedrq pkgs -P <capability> -F name`
  (or `-F source`)
- To check whether a Python project is packaged, query its capability,
  `fedrq pkgs -P 'python3dist(<name>)'`, instead of guessing a package
  name. Only libraries must take the `python3-` prefix; packages that
  mainly provide applications follow the general naming guidelines
  (`mkdocs`, `mkdocs-material`), and a `python3-<name>` virtual provide
  is optional (mkdocs has none). So an empty result for a guessed
  `python3-<name>` does not mean the project is not packaged. Use the
  normalized project name: lowercase, with `_` and `.` as `-`
  (`python3dist(zope-interface)`; `python3dist(zope.interface)` and
  `python3dist(PyYAML)` find nothing)
- `-F source` already prints bare source package names
  (`evolution-data-server`), not NVRs. Do not strip a "version-release"
  suffix with `sed 's/-[^-]*-[^-]*$//'`; it mangles hyphenated names
  (`evolution-data-server` becomes `evolution`)
- `-F source_name` is `(none)` for source RPMs, so with `whatrequires`
  (whose results include source packages via BuildRequires) use
  `-F source`. Filter `(none)` out of results in general
- `-F requires` lists dependency strings; rich/boolean dependencies start
  with `(` and must be handled before feeding the list back into
  `pkgs -P`
- BuildRequires-side reverse dependencies: restrict to source packages
  with `-A src`, e.g.
  `fedrq whatrequires -b rawhide -A src -F name libfoo-devel 'pkgconfig(libfoo)'`

Architectures:
- Queries use the host's architecture. On an aarch64 machine,
  x86_64-only packages are invisible unless `--forcearch x86_64` is
  given. For reverse-dependency sweeps (e.g. a rebuild list), take the
  union over the architectures that matter; packages with
  `ExclusiveArch` appear only on some

Koji and local repositories:
- `-r @koji:<tag>` indexes binary RPMs only, so `subpkgs -S` returns
  nothing for a side tag. Use `-r @koji-src:<tag>` for source RPMs
  (e.g. BuildRequires queries); `fedrq pkgs -r @koji:<tag> '*'` lists the
  tag's binaries, including inherited ones
- A side tag repo is standalone: do not combine `-b` with
  `-r @koji:<tag>`
- `-r @baseurl:file://<dir>` likewise replaces the branch's
  repositories rather than adding to them: with `-b rawhide` as well,
  rawhide's own packages are not found. Query the two separately
- A `mock --localrepo` results directory indexes binary RPMs only: the
  SRPMs sit beside each build but are not in its repodata, so `-A src`
  returns nothing. Read a build's BuildRequires from its SRPM with
  `rpm -qp --requires <srpm>`
- EPEL 10 `@testing` repositories are not supported yet (no metalinks
  exist for `epel10`); such queries fail silently
