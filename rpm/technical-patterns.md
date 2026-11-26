# RPM Technical Patterns

## Core Instructions

- Trace the full packaging logic before flagging issues
- IMPORTANT: never assume a macro expands to a particular value -- verify
  by checking the macro definition or the target distribution's macro set
- IMPORTANT: never skip reviewing a section because another section had issues
- Never report errors without verifying the error can actually occur given
  the spec file context and target distribution

## Spec File Structure

Canonical section ordering:

1. Header (Name, Version, Release, Summary, License, URL, Source, Patch,
   BuildRequires, Requires, etc.)
2. %description
3. %package (subpackages, with their own %description)
4. %prep
5. %build
6. %check
7. %install
8. %files (and subpackage %files)
9. %changelog

## RPM Macros

### System Path Macros
- `%{_prefix}` - /usr
- `%{_bindir}` - /usr/bin
- `%{_sbindir}` - /usr/sbin
- `%{_libdir}` - /usr/lib or /usr/lib64
- `%{_libexecdir}` - /usr/libexec
- `%{_datadir}` - /usr/share
- `%{_sysconfdir}` - /etc
- `%{_localstatedir}` - /var
- `%{_sharedstatedir}` - /var/lib
- `%{_includedir}` - /usr/include
- `%{_mandir}` - /usr/share/man
- `%{_infodir}` - /usr/share/info
- `%{_unitdir}` - /usr/lib/systemd/system
- `%{_userunitdir}` - /usr/lib/systemd/user
- `%{_sysusersdir}` - /usr/lib/sysusers.d
- `%{_tmpfilesdir}` - /usr/lib/tmpfiles.d
- `%{_udevrulesdir}` - /usr/lib/udev/rules.d

### Build Macros
- `%configure` - run ./configure with standard flags
- `%cmake` - run cmake with standard flags
- `%meson` - run meson setup with standard flags
- `%make_build` - run make with parallel flags
- `%make_install` - run make install with DESTDIR
- `%cmake_build` / `%cmake_install`
- `%meson_build` / `%meson_install`

### Conditional Macros
- `%bcond_with foo` - define build conditional (default off)
- `%bcond_without foo` - define build conditional (default on)
- `%{?with_foo:...}` - expand if --with foo
- `%{?fedora}` - defined on Fedora builds
- `%{?rhel}` - defined on RHEL/CentOS builds
- `%if 0%{?fedora} >= 40` - version-conditional blocks

## Dependency Generation

RPM automatically detects:
- ELF shared library dependencies (from linked .so files)
- Python module dependencies (from imports)
- Perl module dependencies
- pkgconfig dependencies
- Ruby gem dependencies

When auto-deps fail or need adjustment:
- `%{?__requires_exclude:...}` - filter auto-requires
- `%{?__provides_exclude:...}` - filter auto-provides
- `AutoReqProv: no` - disable entirely (use sparingly, document why)

## Scriptlet Patterns

### systemd Integration
- `%systemd_post unit.service` - in %post
- `%systemd_preun unit.service` - in %preun
- `%systemd_postun_with_restart unit.service` - in %postun

### User/Group Creation
- Prefer sysusers.d: `%sysusers_create_package name file.conf`
- Legacy: useradd/groupadd in %pre with $1 == 1 guard

### ldconfig
- Modern: `%ldconfig_scriptlets` (or file triggers handle it)
- Legacy: explicit /sbin/ldconfig in %post/%postun

## File Ownership Rules

- Own directories you create, never own system directories
- `%dir %{_sysconfdir}/myapp` - own a config directory
- `%config(noreplace) %{_sysconfdir}/myapp/config.conf` - config file
- `%license LICENSE` - license files
- `%doc README.md` - documentation
- `%ghost %{_localstatedir}/run/myapp.pid` - runtime files

## Common Anti-Patterns

### 1. Hardcoded Paths
```
# WRONG
install -m 755 myapp /usr/bin/myapp

# CORRECT
install -m 755 myapp %{buildroot}%{_bindir}/myapp
```

### 2. Missing %{?dist} in Release
```
# WRONG
Release: 1

# CORRECT
Release: 1%{?dist}
```

### 3. %define vs %global at Top Level
```
# WRONG (lazy evaluation, scoped)
%define commit abc123

# CORRECT (immediate evaluation, global scope)
%global commit abc123
```

### 4. Disabling Auto-Dependencies Without Justification
```
# WRONG - hides real dependency problems
AutoReqProv: no

# CORRECT - filter specific false deps with documentation
%global __requires_exclude ^libprivate\\.so
```

### 5. Overriding Compiler Flags
```
# WRONG - loses distribution hardening flags
export CFLAGS="-O2"

# CORRECT - append to existing flags
export CFLAGS="%{optflags} -Wextra"
```

### 6. BuildRoot References in Scriptlets
```
# WRONG - buildroot does not exist at install time
%post
cat %{buildroot}%{_sysconfdir}/myapp/default.conf

# CORRECT
%post
cat %{_sysconfdir}/myapp/default.conf
```

### 7. Missing %check Section
```
# Not an error if no test suite exists, but if the project has tests:
%check
%make_build check
# or
%ctest
# or
%meson_test
```
