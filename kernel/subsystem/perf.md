# Perf Tools Subsystem Details

## Event Format Changes and Cross-Tool Impact

Changing default event formats (e.g., MMAP to MMAP2) causes NULL pointer
dereferences or missing data in subcommands that only register handlers for
the old format. When an event type arrives without a registered callback, it
is silently ignored, leaving structures like `machine->vmlinux_map` as NULL.

- Each perf subcommand (`tools/perf/builtin-*.c`) populates a
  `struct perf_tool` (defined in `tools/perf/util/tool.h`) with callbacks for
  each event type it processes (`.mmap`, `.mmap2`, `.sample`, `.comm`,
  `.fork`, etc.).
- If a callback is not set for an event type, that event is dropped.
- `perf_event__process_mmap()` and `perf_event__process_mmap2()` in
  `tools/perf/util/event.c` are separate callbacks; registering one does not
  automatically handle the other.
- To find all callback registration sites, search for `\.(mmap|mmap2)\s*=`
  across `tools/perf/builtin-*.c`. Different tools use different variable
  names for their `struct perf_tool` instance (`trace->tool`, `eops`,
  `pdiff.tool`, `sched->tool`, `perf_kmem`, etc.).

Any subcommand that registers `.mmap` but not `.mmap2` (or vice versa) when
both event types may be generated is a bug.

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

## Testing Infrastructure and `fake_pmu`

Failing to handle the `fake_pmu` flag causes test failures when validating
metrics from architectures or PMUs not present on the test machine. Tests
using fake PMUs exercise the metric parser across all architectures without
requiring the actual hardware.

- `struct parse_events_state` (defined in `tools/perf/util/parse-events.h`)
  has a `fake_pmu` boolean field. It is set by metric validation tests
  (see `tools/perf/tests/pmu-events.c`) to parse events and metrics without
  requiring the referenced PMUs to exist.
- When `fake_pmu` is true, the parser accepts PMU names that would otherwise
  fail lookup and uses reasonable fallback values.
- `__parse_events()` in `tools/perf/util/parse-events.c` accepts a
  `bool fake_pmu` parameter and stores it in `parse_events_state`.

Any code that performs PMU lookups by name must provide fallback behavior
when `fake_pmu` is enabled:

- `perf_pmus__find()` returns NULL when the PMU does not exist on the
  current system.
- `perf_cpu_map__new()` returns NULL when the CPU string is unrecognized.
- When both return NULL but `fake_pmu` is true, use a sensible default.
  `get_config_cpu()` in `tools/perf/util/parse-events.c` demonstrates the
  correct pattern: it falls back to `cpu_map__online()`.

```c
// WRONG: Fails in fake_pmu tests
pmu = perf_pmus__find(term->val.str);
if (!pmu) {
    map = perf_cpu_map__new(term->val.str);
    if (!map)
        return -EINVAL;  // Test fails here for cross-arch metrics
}

// CORRECT: Handle fake_pmu case (mirrors get_config_cpu logic)
pmu = perf_pmus__find(term->val.str);
if (pmu) {
    map = perf_cpu_map__get(pmu->cpus);
} else {
    map = perf_cpu_map__new(term->val.str);
    if (!map && fake_pmu)
        map = cpu_map__online();  // Fallback for fake PMU tests
}
```

The `config_term_common()`, `config_term_pmu()`, and `config_attr()` functions
already accept a `struct parse_events_state *parse_state` parameter that
carries `fake_pmu`. Any new parsing or config helper must similarly accept
`parse_state` (not just the error pointer) so `fake_pmu` remains accessible.
Validation errors must be conditional: `if (!map && !parse_state->fake_pmu)`.

## Quick Checks

- **Callback error paths**: When a function takes a callback and iterates
  over a directory, verify that callback errors trigger full cleanup before
  return.
- **Nested `openat`/`fdopendir`**: When iterating nested directories (e.g.,
  `/proc/pid/fd` then `/proc/pid/fdinfo`), track each resource separately
  and verify cleanup ordering.
- **Event handler completeness**: When modifying which events are generated,
  verify all consuming tools handle both old and new event types.

## perf.data Header Validation

Header processing functions in `perf.data` populate fields in
`struct perf_env` and may depend on fields that were populated by
earlier headers. When a header processing function accesses
`perf_env` fields that are populated by a different header, it
must verify those fields have been initialized. Headers can
appear out of order in `perf.data` files, and older files may
omit headers entirely.

- `process_cpu_domain_info()` depends on CPU count data
  populated by `process_nr_cpus()`, so `HEADER_NRCPUS` must be
  processed before `HEADER_CPU_DOMAIN_INFO`.
- If a prerequisite header was not present in the file, the
  dependent fields in `perf_env` remain zero-initialized or
  NULL.
- Functions that skip validation of prerequisite fields will
  dereference NULL pointers or operate on zero-length arrays
  when processing files that lack the prerequisite header or
  present headers out of order.

Any header processing function that accesses `perf_env` fields
populated by a different header without first verifying those
fields are initialized is a bug.
