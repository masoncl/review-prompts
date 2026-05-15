# Perf Tools Subsystem Details

## Tool API Callbacks

Omitting event callbacks in `struct perf_tool` causes incoming events to be
silently dropped. In pipe mode, dropping `perf_event_header_attr` events
prevents the creation of evlists/evsels, breaking event processing entirely.

- Unregistered event types are silently ignored
- Any tool registering `.mmap` must also register `.mmap2` (and vice versa)
- In pipe mode, verify tools correctly register attribute and feature callbacks
  to populate evsels and `struct perf_env`

## Build System Feature Detection

Incomplete refactoring of feature detection causes build failures when
optional libraries are not installed. The fast-path `test-all.bin` target
links against all default feature libraries at once; if any library is
missing, the fast path fails and falls back to slow individual feature tests.
When making a feature opt-in, leftover library references in unconditional
scope break builds on systems without those libraries.

- `tools/build/feature/test-all.c` includes and calls all default feature
  test functions. This file is compiled into `test-all.bin` to check if all
  default features can compile and link together.
- `tools/build/feature/Makefile` defines `BUILD_ALL` with the combined
  linker flags needed for `test-all.bin`. Individual feature test recipes
  specify their own flags inline (e.g., `$(BUILD) -lpthread`), with the
  exception of `BUILD_BFD`.
- `tools/perf/Makefile.config` defines `FEATURE_CHECK_LDFLAGS-<feature>`
  variables for each optional feature's linker flags.

When removing a feature test from `test-all.c` (e.g., making it conditional
on `BUILD_NONDISTRO`), the following must also move to the same conditional
scope:

1. `FEATURE_CHECK_LDFLAGS-<feature>` assignments in `Makefile.config`
2. Library references (`-l<name>`) in `BUILD_ALL` in
   `tools/build/feature/Makefile`
3. Any fallback link attempts in the `test-all.bin` recipe

Build system changes typically affect multiple files that must stay
consistent:
- `tools/build/feature/test-all.c` -- feature test code
- `tools/build/feature/Makefile` -- feature build rules and `BUILD_ALL`
- `tools/perf/Makefile.config` -- feature flags and library assignments

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

## Quick Checks

- **Callback error paths**: When a function takes a callback and iterates
  over a directory, verify that callback errors trigger full cleanup before
  return.
- **Nested `openat`/`fdopendir`**: When iterating nested directories (e.g.,
  `/proc/pid/fd` then `/proc/pid/fdinfo`), track each resource separately
  and verify cleanup ordering.
- **Tool API callbacks**: Verify subcommands register complete event callbacks (pairing `.mmap`/`.mmap2` and handling `.attr` in pipe mode).
- **`perf_env` validation**: Verify `perf_env` fields are checked for initialization before access.
