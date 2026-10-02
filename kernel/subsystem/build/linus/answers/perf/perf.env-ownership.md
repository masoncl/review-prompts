- Global env: none. There is no perf_env__host(); each live user declares its
  own `struct perf_env host_env` (search `host_env` under `tools/perf`).
- `perf_session__env()`: returns `&session->header.env` for every kind of
  session, including live ones.
- `session->machines.host.env` is a second route and is not always the same
  object:

  | Session | `perf_session__env()` | `session->machines.host.env` |
  |---|---|---|
  | read, file or pipe | `header.env`, filled from the input | same object, set in `perf_session__read_header()` |
  | write (`perf record`) | `header.env` | NULL |
  | `data == NULL` (live) | `header.env`; `__perf_session__new()` only `perf_env__init()`s it | the caller's `host_env` |

- Guest machines: `machine->env` stays NULL from `machine__init()`.
- `__perf_session__new()` with `data == NULL`: `assert(host_env != NULL)`, then
  stores the pointer; nothing is copied.
- `perf_session__new()`: passes NULL for `host_env`, so it cannot be used
  without a `struct perf_data`.
- `host_env` lifetime: the caller owns it; `perf_session__delete()` calls
  `perf_env__exit()` on `session->header.env` only.
- `perf_env__set_cmdline()`: not called by `__perf_session__new()`; callers
  call it on their `host_env`, as `cmd_top()` does.
- `cmd_top()` in `tools/perf/builtin-top.c`: fills `host_env` eagerly with
  cmdline, `perf_env__read_cpuid()` and, with branch stacks,
  `perf_env__read_core_pmu_caps()`; with `HAVE_LIBBPF_SUPPORT`, BPF side-band
  data also goes to `host_env`.
- `cmd_top()` data in `host_env` is not visible through
  `perf_session__env(top->session)`.
- perf trace live: no session; `trace->host_env` is passed to
  `machine__new_host()`, so the env is reached as `machine->env`, not through
  a session.
- `struct evlist`: has no `env` member, only a `session` back-pointer set by
  `evlist__set_session()`.
- `evsel__env()`: returns `perf_session__env()` of the evlist's session, or
  NULL when the evsel has no evlist or the evlist has no session.
- Pipe fill: `PERF_RECORD_HEADER_FEATURE` reaches `tool->feature`;
  `perf_tool__init()` installs `process_event_op2_stub()`, so no header
  feature reaches the env unless the tool sets `feature` to
  `perf_event__process_feature()` or a wrapper.
- Regular file, `nr_cpus_avail` still 0 after the sections:
  `perf_session__read_header()` sets it to `MAX_NR_CPUS`; the pipe path returns
  before this.
- Header `write` callbacks: some use `ff->ph->env`, for example
  `write_cmdline()` and `write_cpu_topology()`; the latter fills `env->cpu`
  through `perf_env__read_cpu_topology_map()`.
