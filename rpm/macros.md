# RPM Macro Reference

## When to Load

Load this file when reviewing macro usage, custom macro definitions,
or complex conditional logic in spec files.

## Macro Definition and Scope

### %global vs %define
```
# %global: immediate evaluation, available everywhere in spec
%global majorver 3

# %define: lazy evaluation, scoped to current context
%define localvar something
```

**Rule**: Use `%global` for top-level spec macro definitions. Use `%define`
only inside macro bodies or when lazy evaluation is specifically needed.

### Macro Parameters
```
# Macro with parameters
%global mymacro() echo %1 %2

# Usage
%mymacro hello world
```

## Path Macros

### Standard Directories
| Macro | Expands to | Use for |
|-------|-----------|---------|
| `%{_prefix}` | /usr | Base prefix |
| `%{_bindir}` | /usr/bin | User commands |
| `%{_sbindir}` | /usr/sbin | Admin commands |
| `%{_libdir}` | /usr/lib[64] | Libraries (arch-specific) |
| `%{_libexecdir}` | /usr/libexec | Internal executables |
| `%{_datadir}` | /usr/share | Arch-independent data |
| `%{_sysconfdir}` | /etc | Configuration files |
| `%{_localstatedir}` | /var | Variable data |
| `%{_sharedstatedir}` | /var/lib | Persistent variable data |
| `%{_rundir}` | /run | Runtime data |
| `%{_includedir}` | /usr/include | Header files |
| `%{_mandir}` | /usr/share/man | Man pages |
| `%{_infodir}` | /usr/share/info | Info pages |
| `%{_docdir}` | /usr/share/doc | Documentation |

### systemd Directories
| Macro | Expands to | Use for |
|-------|-----------|---------|
| `%{_unitdir}` | /usr/lib/systemd/system | System units |
| `%{_userunitdir}` | /usr/lib/systemd/user | User units |
| `%{_sysusersdir}` | /usr/lib/sysusers.d | User/group definitions |
| `%{_tmpfilesdir}` | /usr/lib/tmpfiles.d | tmpfiles configuration |
| `%{_presetdir}` | /usr/lib/systemd/system-preset | Service presets |
| `%{_modulesloaddir}` | /usr/lib/modules-load.d | Kernel module loading |
| `%{_sysctl_dir}` | /usr/lib/sysctl.d | Sysctl configuration |

### Other Standard Directories
| Macro | Expands to | Use for |
|-------|-----------|---------|
| `%{_udevrulesdir}` | /usr/lib/udev/rules.d | udev rules |
| `%{_tmppath}` | /var/tmp | Build temp directory |
| `%{_pkgdocdir}` | %{_docdir}/%{name} | Package documentation |

## Build System Macros

### autotools
```
%configure          # runs ./configure with standard flags
%make_build         # runs make with -j flags
%make_install       # runs make install DESTDIR=%{buildroot}
```

### CMake
```
%cmake              # runs cmake with standard flags
%cmake_build        # builds the cmake project
%cmake_install      # installs the cmake project
```

### Meson
```
%meson              # runs meson setup
%meson_build        # builds the meson project
%meson_install      # installs the meson project
%meson_test         # runs meson test
```

### Python
See `ecosystem/python.md` for full Python packaging guidance.
```
# Modern (pyproject.toml)
%pyproject_wheel     # build wheel
%pyproject_install   # install wheel
%pyproject_check_import  # verify imports work

# Legacy (setup.py)
%py3_build          # python3 setup.py build
%py3_install        # python3 setup.py install
```

## Conditional Build Macros

### bcond Pattern
```
# Default off (user enables with --with foo)
%bcond_with foo

# Default on (user disables with --without bar)
%bcond_without bar

# Usage in spec
%if %{with foo}
BuildRequires: libfoo-devel
%endif
```

### Distribution Version Checks
```
# Fedora-only
%if 0%{?fedora}
Requires: fedora-specific-package
%endif

# Fedora 40+
%if 0%{?fedora} >= 40
# use newer feature
%endif

# RHEL/CentOS
%if 0%{?rhel}
Requires: rhel-specific-package
%endif

# RHEL 9+
%if 0%{?rhel} >= 9
# use newer feature
%endif
```

## Common Macro Mistakes

### 1. Using %define at Top Level
```
# WRONG
%define version 1.2.3

# CORRECT
%global version 1.2.3
```

### 2. Hardcoding Paths
```
# WRONG
install -D -m 755 myapp /usr/bin/myapp

# CORRECT
install -D -m 755 myapp %{buildroot}%{_bindir}/myapp
```

### 3. Not Quoting %{?dist}
```
# WRONG (fails if dist is not defined)
Release: 1%{dist}

# CORRECT (gracefully empty if undefined)
Release: 1%{?dist}
```

### 4. Using Obsolete Macros
```
# WRONG (obsolete)
%{__rm} -rf %{buildroot}
%{__install} -m 644 file %{buildroot}%{_datadir}/

# CORRECT (just use the commands directly)
rm -rf %{buildroot}
install -m 644 file %{buildroot}%{_datadir}/
```

### 5. Wrong %if Syntax for Distro Checks
```
# WRONG (string comparison, not numeric)
%if %{?fedora}

# CORRECT (numeric comparison with fallback to 0)
%if 0%{?fedora}
```
