# RPM License Handling

## When to Load

Load this file when reviewing the License: field, %license directives,
or when license compliance questions arise.

## SPDX License Identifiers

### Fedora (F38+)
Fedora requires SPDX license expressions in the License: field.

```
# Single license
License: MIT
License: GPL-2.0-only
License: Apache-2.0

# Combined licenses (AND = all apply, OR = choice)
License: MIT AND BSD-3-Clause
License: GPL-2.0-or-later OR MIT

# With exceptions
License: GPL-2.0-only WITH Classpath-exception-2.0
```

### Common SPDX Identifiers
| SPDX | Legacy (pre-F38) | Notes |
|------|------------------|-------|
| `MIT` | `MIT` | Same |
| `GPL-2.0-only` | `GPLv2` | |
| `GPL-2.0-or-later` | `GPLv2+` | |
| `GPL-3.0-only` | `GPLv3` | |
| `GPL-3.0-or-later` | `GPLv3+` | |
| `LGPL-2.1-only` | `LGPLv2` | |
| `LGPL-2.1-or-later` | `LGPLv2+` | |
| `Apache-2.0` | `ASL 2.0` | |
| `BSD-2-Clause` | `BSD` | |
| `BSD-3-Clause` | `BSD` | |
| `MPL-2.0` | `MPLv2.0` | |
| `ISC` | `ISC` | Same |
| `Zlib` | `zlib` | Case difference |

### CentOS Stream / RHEL
- RHEL 9+ generally follows Fedora SPDX adoption
- Older packages may still use legacy identifiers
- EPEL follows the guidelines of the target EL release

## License Field Format

### Single License
```
License: MIT
```

### Multiple Licenses (all apply to different parts)
```
License: MIT AND BSD-3-Clause
```

### Choice of License
```
License: GPL-2.0-or-later OR MIT
```

### Complex Combinations
```
License: (MIT OR Apache-2.0) AND BSD-3-Clause
```

## %license Directive

### Usage in %files
```
%files
%license LICENSE COPYING
%doc README.md
```

### Key Rules
- Use `%license` for all license files (not `%doc`)
- `%license` files are installed to `%{_licensedir}/%{name}`
- Available since RPM 4.11 (Fedora 21+, RHEL 7+)
- Multiple license files are supported

### Subpackage Licenses

A subpackage only needs its own `%license` directive if it can be installed
without pulling in another subpackage that already ships the license file.

```
# -libs is installable on its own -- must ship %license
%files libs
%license LICENSE

# -devel requires -libs (which ships %license) -- duplication NOT needed
%files devel
%{_includedir}/%{name}
%{_libdir}/lib%{name}.so
```

**Rule**: Check the subpackage's `Requires:` chain. If any hard dependency
already ships `%license`, the subpackage does not need to duplicate it.

Subpackages that MAY need their own `%license`:
- `-doc` with `BuildArch: noarch` (can be installed on a different arch
  without the main package)
- Any subpackage installable independently of the license-carrying package

## License Audit

### What to Verify
1. License: field matches the actual license files in the source
2. All license files listed with %license in %files
3. If sources contain multiple licenses, License: field reflects all of them
4. Bundled dependencies' licenses are included in the License: field

### Where to Look
- `LICENSE`, `COPYING`, `NOTICE` files in source root
- License headers in source files
- Bundled/vendored dependency licenses
- Documentation licenses (may differ from code license)

### Red Flags
- No license file in upstream source
- License: field says MIT but source headers say GPL
- Bundled dependencies with incompatible licenses
- Missing license for a significant component
