- normalize_arch(), perf_env__raw_arch(), perf_env__read_arch(),
  perf_env__init_nodes(), perf_env__find_pmu_caps() and evsel__get_arch() do
  not exist here; the raw recorded string is the field `env->arch`.
- `perf_env__arch()`: maps `perf_env__e_machine()` to a static perf arch name
  such as "x86", "arm64" or "powerpc"; never NULL, never the `uname()` string,
  and it does not write `env->arch`.
- `perf_env__e_machine()` in `tools/perf/util/env.c`: the accessor used for
  arch decisions, compared with `EM_` constants; see
  `evlist__init_trace_event_sample_raw()` in `tools/perf/util/sample-raw.c`.
- `env->arch != NULL`: the in-tree test for "recorded, not live"; for example
  `perf_env__lookup_objdump()` in `tools/perf/arch/common.c` returns early
  when it is NULL.
- `perf_env__os_release()`: with `env->os_release` unset, returns NULL when
  `env->arch` is set and fills from `uname()` only when it is not; a NULL env
  gives `perf_version_string`.
- `env->lock`: taken only by `perf_env__os_release()`; the other lazy
  accessors fill their fields without it.
- NULL env is accepted by `perf_env__arch()`, `perf_env__e_machine()`,
  `perf_env__e_machine_nocache()`, `perf_env__nr_cpus_avail()` and
  `perf_env__os_release()`; the other accessors in `tools/perf/util/env.c` and
  `perf_env__get_cpu_topology()` have no NULL test of `env`.
- `perf_env__get_cpu_topology()`: static inline in `tools/perf/util/env.h`;
  returns `&env->cpu[cpu.cpu]`, or NULL when `env->cpu` is NULL or the cpu is
  outside `[0, env->nr_cpus_avail)`; it fills nothing.
- `perf_env__get_cpu_topology()` in use: for example
  `perf_env__get_socket_aggr_by_cpu()` in `tools/perf/builtin-stat.c`, which
  leaves the id empty on NULL.
- `perf_env__numa_node()`: its only caller is
  `perf_env__get_node_aggr_by_cpu()` in `tools/perf/builtin-stat.c`.
- `env->nr_cpus_avail == 0`: not a test for a missing `HEADER_NRCPUS` on a
  regular file, see "Environment ownership"; it is 0 in a record session until
  `write_cpu_topology()` runs.
- **Potentially unsafe usage**: indexing `env->cpu[]` directly.
  - Unsafe: with a cpu from a sample or cpu map when nothing has shown
    `env->cpu` non-NULL; `process_cpu_topology()` in
    `tools/perf/util/header.c` leaves it NULL for old-format data while
    `nr_cpus_avail` is set.
  - Safe: through `perf_env__get_cpu_topology()` with a NULL test, as
    `perf_env__get_core_aggr_by_cpu()` does.
  - Safe: after `perf_env__read_cpu_topology_map()` returned 0, with the index
    bounded by `env->nr_cpus_avail`, as `write_cpu_topology()` does.
- **Potentially unsafe usage**: passing a wider cpu number to
  `perf_env__get_cpu_topology()`.
  - Unsafe: when the value was not range-checked first; `struct perf_cpu`
    holds an `int16_t`, so a large value wraps to a valid index.
  - Safe: when the wide value is known to be below `env->nr_cpus_avail` and
    inside the `int16_t` range before the `struct perf_cpu` is built:
    `machine__resolve()` in `tools/perf/util/event.c` compares `al->cpu` with
    `env->nr_cpus_avail`, and for a sample that came through
    `perf_session__deliver_event()` that function has already clamped
    `sample.cpu` below `MAX_NR_CPUS`, other than `(u32)-1`, which the
    `al->cpu >= 0` test in `machine__resolve()` rejects.
- **Potentially unsafe usage**: dereferencing the result of `evsel__env()` or
  `machine->env`.
  - Unsafe: when the evlist has no session, or the machine is a guest or the
    host of a write-mode session; the pointer is NULL.
  - Safe: test first, as `thread__resolve_callchain_sample()` in
    `tools/perf/util/machine.c` and `format_field__get_cpumask()` in
    `tools/perf/util/evsel.c` do.
  - Safe: `perf_session__env()` on a valid session; it returns the address of
    an embedded member.
