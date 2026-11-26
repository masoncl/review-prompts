# Python Packaging

## When to Load

Load when the spec uses `%pyproject_*` or `%py3_*` macros,
`%{python3_sitelib}` / `%{python3_sitearch}`, BuildRequires `python3-devel`,
the package is named `python-*`, or the sources contain `pyproject.toml`,
`setup.py`, or `setup.cfg`.

References:
- https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/
- https://src.fedoraproject.org/rpms/pyproject-rpm-macros (README is the
  macro reference)

## Standard Spec Shape

```
Name:           python-foo
Version:        1.2.3
Release:        %autorelease
Summary:        ...
License:        MIT
URL:            https://github.com/example/foo
Source:         %{pypi_source foo}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
...}

%description %_description

%package -n     python3-foo
Summary:        %{summary}

%description -n python3-foo %_description

%prep
%autosetup -p1 -n foo-%{version}

%generate_buildrequires
%pyproject_buildrequires -t

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l foo

%check
%pyproject_check_import
%tox

%files -n python3-foo -f %{pyproject_files}
%doc README.md
```

## Review Checks

- [ ] Uses pyproject-rpm-macros (`%pyproject_wheel` / `%pyproject_install`),
      not the deprecated `%py3_build` / `%py3_install` (setup.py-based
      macros are deprecated in Fedora; flag as MEDIUM for new packages)
- [ ] `%pyproject_buildrequires` used for BuildRequires; extras/test
      requirements pulled via `-x <extra>`, `-t` (tox), `-g <group>` (if
      supported in target), rather than hand-listed
- [ ] `%pyproject_save_files` names the top-level module(s) and the result
      is used via `%files -f %{pyproject_files}`; `-l` asserts a license
      file was found
- [ ] `%pyproject_check_import` and/or real tests (`%pytest`, `%tox`) in
      `%check`
- [ ] Binary subpackage named `python3-<name>`; the `python-<name>` SRPM
      naming follows normalized PyPI name
- [ ] `BuildArch: noarch` for pure-Python; arch-specific packages install
      to `%{python3_sitearch}`
- [ ] Upper version pins in upstream metadata removed in `%prep` (sed /
      patch) only with a comment, not by hand-maintained BuildRequires
- [ ] No byte-compiled files or `__pycache__` shipped from sources;
      bytecompilation is done by the brp script
- [ ] Unversioned `python` shebangs fixed (`%py3_shebang_fix` or brp
      handles it)
- [ ] Tests needing network skipped selectively
      (`%pytest -k "not test_net"` / `--deselect`) with a comment

## Build Failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `%generate_buildrequires` fails with `No matching package to install: python3dist(foo) < 2` | Upstream upper pin that Fedora's version exceeds | Relax the pin in `%prep` with a comment, or patch upstream |
| `ModuleNotFoundError: No module named 'distutils'` | Python >= 3.12 removed distutils | Use setuptools; backport upstream fix |
| `ModuleNotFoundError` for `cgi`, `telnetlib`, `imp`, `asynchat`, etc. | Modules removed in Python 3.12/3.13 (PEP 594) | Patch to use replacements; check for the legacy-cgi / standard-* compat packages |
| `%pyproject_save_files` errors: `No matching files` / unknown module | Wrong module name passed, or package installs into a different top-level name | Inspect `%{buildroot}%{python3_sitelib}`; pass the actual top-level module(s) or `'*'` with care |
| `%pyproject_save_files -l` fails: no license files | Upstream metadata does not declare license files | Add `%license` manually and drop `-l`, or use `-L` |
| Tests import from the source tree instead of the installed package | Tests run without `PYTHONPATH` pointing at buildroot | Use `%pytest` / `%tox` macros which set paths; avoid `python3 -m pytest` from source dir |
| `pip` tries to reach PyPI | Build isolation or raw `pip install` used | Use `%pyproject_wheel`; it builds without isolation and offline |
| Failures after Python version bump | Removed stdlib modules/APIs, deprecation warnings turned errors in tests (`-W error`), C-API changes for extensions | Check the Python Change page porting notes; patch or backport |
| C extension compile failures after bump | Removed/changed C-API (e.g. private `_Py*` APIs) | Backport upstream, or update to version supporting the new Python |

## False Positives

- No explicit `Requires: python3-foo` runtime deps: generated automatically
  from installed metadata (`python3dist(...)`)
- No `Provides: python3-foo` / `%py_provides`: Fedora auto-generates
  `python3-<name>` provides; `%py_provides` is only needed for alternative
  names
- `%files` without explicit module paths when `-f %{pyproject_files}` is used
- `.dist-info` directory in `%files`: required metadata, included by
  `%pyproject_save_files`
- Missing `%{?_isa}` on `python3dist()` dependencies: these are not
  arch-qualified
- Using `%{python3_sitelib}` in a noarch package or `%{python3_sitearch}`
  in an arch-specific one is correct; only flag a mismatch between the
  macro and `BuildArch`
