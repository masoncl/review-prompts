# Language Ecosystem Guides Index

## Purpose

Many packages are built with a language-specific toolchain and a dedicated
macro set (cargo-rpm-macros, go-rpm-macros, pyproject-rpm-macros, ...).
These ecosystems have their own guidelines, generators, and failure modes
that general RPM knowledge does not cover.

Each ecosystem file has three sections:
- **Review checks**: used by `review-core.md`
- **Build failures**: used by `debugging.md`
- **False positives**: used during verification (`false-positive-guide.md`)

Load the matching file whenever any trigger below is present. A package can
match more than one ecosystem (e.g. a Python extension written in Rust);
load all matching files.

## Detection

| Ecosystem | Triggers | File |
|-----------|----------|------|
| Rust | `%cargo_*` macros, `BuildRequires: cargo-rpm-macros` / `rust-packaging`, `%{crates_source}`, Name `rust-*`, `Cargo.toml` / `Cargo.lock` in sources, `rust2rpm.toml` | `rust.md` |
| Go | `%gometa`, `%goprep`, `%gobuild`, `%{goipath}`, `BuildRequires: go-rpm-macros` / `go-vendor-tools`, Name `golang-*`, `go.mod` in sources, `go-vendor-tools.toml` | `golang.md` |
| Python | `%pyproject_*`, `%py3_*`, `%{python3_sitelib}` / `%{python3_sitearch}`, `BuildRequires: python3-devel`, Name `python-*` / `python3-*`, `pyproject.toml` / `setup.py` in sources | `python.md` |

## General Principles Across Ecosystems

- Prefer the ecosystem's spec generator output (rust2rpm, go2rpm,
  pyp2spec) as the baseline; deviations from generated specs should have
  a reason
- Ecosystem macros set distribution flags, offline mode, and
  debuginfo-friendly build options. Calling the raw tool (`cargo build`,
  `go build`, `pip install`) directly usually loses some of this
- Dependency generators exist for all three; hand-written Requires that
  duplicate generated ones are redundant
- Bundled/vendored dependencies must be declared with
  `Provides: bundled(...)` and their licenses reflected in `License:`
- Builds run without network access; anything that downloads at build
  time will fail in koji/mock
