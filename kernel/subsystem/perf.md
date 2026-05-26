# Perf Tools Subsystem Details

## Tool API Callbacks

Omitting event callbacks in `struct perf_tool` causes incoming events to be
silently dropped. In pipe mode, dropping `perf_event_header_attr` events
prevents the creation of evlists/evsels, breaking event processing entirely.

- Unregistered event types are silently ignored
- Any tool registering `.mmap` must also register `.mmap2` (and vice versa)
- In pipe mode, verify tools correctly register attribute and feature callbacks
  to populate evsels and `struct perf_env`

## Build Feature Detection and Conditional Compilation

Inconsistent feature detection flags cause build failures or missing
functionality when optional libraries are omitted. When a feature test succeeds,
`Makefile.config` defines `-DHAVE_*_SUPPORT` flags; omitting these defines or
failing to provide header fallback stubs breaks compilation on systems lacking
the library.

- Feature checks (`tools/build/feature/test-*.c`) verify optional library
  availability during build
- `tools/perf/Makefile.config` evaluates feature test results and sets compiler
  flags (e.g., `CFLAGS += -DHAVE_LIBELF_SUPPORT` or `CONFIG_*` defines)
- C code must guard feature-dependent logic with `#ifdef HAVE_*_SUPPORT` or
  using `CONFIG_*` values in the Build or Makefile
- Header files must provide compatible dummy inline stubs (e.g., returning
  `-ENOTSUPP` or `NULL`) when the feature define is absent
- When adding or modifying a feature, ensure `Makefile.config`, feature
  makefiles, and header guards remain strictly synchronized

## perf.data Header Validation

A `perf.data` file may be a regular file or come from a pipe. When accessing
events in pipe mode, the stream doesn't support seek. A regular file contains
sections for attributes and for features; in pipe mode, these must be handled as
synthesized events.  New features will be unknown and unsupported by old perf
tools, whilst `perf.data` files from old perf tools won't contain the new
features. The loaded features are put in `struct perf_env`, which is typically
populated by `perf_session__new()`, but in pipe mode, events need processing to
fill in the `perf_env`. In live mode (like `perf top`), the host `perf_env` is
explicitly created. Accessing `perf_env` fields without first verifying those
fields are initialized is a bug.

## Architecture-Specific Code and Cross-Platform Analysis

Placing analysis or decoding logic in `tools/perf/arch/` restricts that
functionality to host binaries compiled for that specific architecture. This
breaks cross-platform analysis, preventing a perf binary on x86 from inspecting
or reporting on a `perf.data` file recorded on ARM or RISC-V.

- The `tools/perf/arch/` directory must only contain code strictly tied to host
  execution (such as native PMU probing or hardware registers)
- Discourage adding new logic to `tools/perf/arch/`; prefer cross-platform
  implementations
- To handle architectural variations during recording or analysis, inspect the
  ELF machine constant (`e_machine`) dynamically available via `struct
  perf_env`, session, machine, thread, or evsel structures

## Reference Count Checking and Pointer Handles

Failing to balance reference counts in perf tools causes memory leaks or
use-after-free defects. When built with `REFCNT_CHECKING` (enabled by
ASAN/LSAN), perf wraps reference-counted structs (e.g., `thread`, `maps`, `dso`)
into intermediary pointer handles (`DECLARE_RC_STRUCT`). Accessing a handle
after calling `_put()` triggers immediate ASAN heap-use-after-free traps, while
missing `_put()` calls trigger LSAN leaks at the exact `_get()` call site.

- Every reference handle acquired via `_get()` (e.g., `thread__get()`,
  `maps__get()`) or allocated via `_new()` must be strictly paired with a
  matching `_put()` (e.g., `thread__put()`)
- When a struct is passed to `_put()`, its pointer handle is invalidated and
  freed; never access struct fields after calling `_put()`
- Avoid raw pointer assignment for reference-counted structs; use explicit
  `_get()` and `_put()` lifecycle helpers

## Quick Checks

- **Callback error paths**: When a function takes a callback and iterates
  over a directory, verify that callback errors trigger full cleanup before
  return.
- **Nested `openat`/`fdopendir`**: When iterating nested directories (e.g.,
  `/proc/pid/fd` then `/proc/pid/fdinfo`), track each resource separately
  and verify cleanup ordering.
- **Tool API callbacks**: Verify subcommands register complete event callbacks (pairing `.mmap`/`.mmap2` and handling `.attr` in pipe mode).
- **Feature detection guards**: Verify optional feature logic is correctly guarded with `HAVE_*_SUPPORT` or `CONFIG_*` defines and accompanied by header fallback stubs.
- **`perf_env` validation**: Verify `perf_env` fields are checked for initialization before access.
- **Cross-platform analysis**: Verify architecture-specific logic queries `e_machine` dynamically rather than relying on hardcoded `tools/perf/arch/` host binaries.
- **Reference count balancing**: Verify every `_new` and `_get` pointer handle is paired with a matching `_put` before pointer scope ends.
