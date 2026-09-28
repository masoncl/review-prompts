# Build and Test Guidance

## Build Configurations

Pahole uses CMake. Its normal `-DLIBBPF_EMBEDDED=ON` configuration builds with
the repository's embedded `lib/bpf/`; `-DLIBBPF_EMBEDDED=OFF` discovers and
uses the available system libbpf. Review CMake changes in both paths when they
touch libbpf, include directories, linking, or feature checks. The selected
library also determines runtime BTF feature availability for that binary.

Typical local build:

```sh
cmake -S . -B build
cmake --build build
cmake --build build --target check
```

### Testing libbpf Changes Before the Submodule Sync

When validating pahole support for a libbpf change that exists in a kernel tree
but has not yet reached the `libbpf/libbpf` GitHub mirror and pahole submodule,
build libbpf directly from that kernel tree and test pahole against it as a
system library:

```sh
make -C /path/to/linux/tools/lib/bpf
sudo make -C /path/to/linux/tools/lib/bpf install
cmake -S . -B build-system-libbpf -DLIBBPF_EMBEDDED=OFF
cmake --build build-system-libbpf
```

`-DLIBBPF_EMBEDDED=OFF` is essential: otherwise the pahole build continues to
use `lib/bpf/` from its submodule and does not exercise the new kernel-tree
API. The system installation must be discoverable by `pkg-config`; set its
search path through the platform-appropriate package configuration when it is
installed outside the default prefix. Run the relevant feature/reporting tests
with this build, then also test the unavailable-API fallback using an older
system libbpf or the current embedded submodule as appropriate.

The `check` target runs `tests/tests` with the build directory on `PATH`. Many
tests compile their own small fixtures, but the broader suite commonly needs a
kernel `vmlinux` that retains DWARF debug information. A kernel build tree with
such a `vmlinux` is therefore useful for local testing; pass it with
`tests/tests --vmlinux /path/to/vmlinux` or set `VMLINUX`. The suite also has
optional dependencies on `bpftool`, toolchains, or network access. Distinguish
an environmental skip (including a missing DWARF-enabled `vmlinux`) from a
regression.

## GitHub Actions Coverage

GitHub Actions is part of the test story and should be considered when
reviewing changes that affect portability, kernel BTF output, or generated
function prototypes:

- `build.yml` builds in Debian with the default compiler, GCC 12, and Clang.
- `lint.yml` runs ShellCheck for shell-script changes.
- `test.yml` invokes the reusable `vmtest.yml` workflow across x86-64 and
  arm64, with GCC and Clang. It builds and installs the current pahole, builds
  a bpf-next kernel using it, supplies that DWARF-enabled `vmlinux` to the
  repository test suite, and compares `pfunct --format_path=btf` output
  against the baseline branch.
- `ondemand.yml` exposes the same VM integration path with selectable kernel,
  architecture, LLVM version, pahole revision, and runner.

Use a focused local fixture to establish a regression quickly; GitHub Actions
provides the broader cross-toolchain and kernel-integration validation. For a
change in the shared formatter or function type path, the CI function comparison
is especially relevant, but it does not replace an assertion for the specific
new behavior.

## Focused Tests

`tests/tests -v <number>` runs selected numbered tests. Before invoking a
number, read the runner’s current numbering and the target script: numbering
changes over time. Tests may preserve failed artifacts below `/tmp/pahole-tests/`.

For a new regression test:

1. Add a narrowly named shell test to `tests/`.
2. Source the existing test helpers and compile a minimal fixture in its
   temporary directory.
3. Cover the prior failure and one meaningful boundary/negative case.
4. Make toolchain- or feature-specific requirements a clear skip, not a false
   pass or an unconditional failure on unsupported hosts.

## What to Flag

- A code change without a test when an isolated fixture can reproduce it.
- A test that uses an installed system `pahole` instead of the built binary.
- A CMake change that makes one libbpf mode implicitly depend on the other.
- Checked-in build directories, generated binaries, coverage profiles, or
  transient test artifacts.
