- `trace_event_raw_event_<class>()`: disables preemption itself with
  `guard(preempt_notrace)()` and then calls
  `do_trace_event_raw_event_<class>()`, which holds the reserve, assign and
  commit steps; see `include/trace/trace_events.h`.
- There is no __DO_TRACE() here; `__do_trace_<name>()` and
  `__DO_TRACE_CALL()` do that job.
- `DECLARE_EVENT_SYSCALL_CLASS()`: the probe differs from the normal one only
  by `might_fault()` before the same `guard(preempt_notrace)()`.
- `perf_trace_<class>()` in `include/trace/perf.h`: same wrapper pattern
  around `do_perf_trace_<class>()`.
- `tracing_gen_ctx_dec()` in `trace_event_buffer_reserve()`: under
  `CONFIG_PREEMPTION` it subtracts the probe's own increment so the record
  shows the call site's preempt count; without it nothing is subtracted.
- Commit: `trace_event_buffer_commit()`; there is no separate filter-aware
  commit call in the probe.
- `DEFINE_EVENT()`: generates no output function and no format; `event_<name>`
  points at `trace_event_type_funcs_<class>` and `print_fmt_<class>`. Only
  `DEFINE_EVENT_PRINT()` generates its own pair.
- Shared per class beyond the ftrace objects: `perf_trace_<class>()` under
  `CONFIG_PERF_EVENTS`, `__bpf_trace_<class>()` under `CONFIG_BPF_EVENTS`, and
  under `CONFIG_BPF_EVENTS` with `CONFIG_DEBUG_INFO_BTF` the id list from
  `_TRACE_BTF_IDS_DECLARE()`.
