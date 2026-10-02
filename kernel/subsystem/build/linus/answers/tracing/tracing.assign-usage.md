- Call-site arguments: evaluated on every call, event enabled or not;
  `trace_<name>()` is a static inline that tests the key inside its body.
- With `CONFIG_TRACEPOINTS=n`: `trace_<name>()` is an empty inline and
  arguments with side effects are still evaluated.
- `TP_STRUCT__entry()` source and length expressions: run in
  `trace_event_get_offsets_<class>()`, before the reserve and before
  `TP_fast_assign()`, also when the reserve then fails.
- `do_perf_trace_<class>()`: runs those expressions before it tests whether
  any perf event is attached on this CPU.
- **Potentially unsafe usage**: a function call or side effect in a call-site
  argument.
  - Unsafe: when the work is only for the event and is costly or takes a lock;
    it runs with the event disabled.
  - Safe: pass the object and compute in the block, as `sched_switch` does
    with `__trace_sched_switch_state()` in `include/trace/events/sched.h`.
  - Safe: prepare inside `if (trace_<name>_enabled())`, as
    `__smp_call_single_queue()` in `kernel/smp.c`.
- **Potentially unsafe usage**: dereferencing a pointer argument in
  `TP_fast_assign()` or in a `TP_STRUCT__entry()` expression.
  - Unsafe: when a call site can pass NULL; the probe dereferences it in the
    caller's context.
  - Safe: test it in the expression, as `nfsd_handle_dir_event` in
    `fs/nfsd/trace.h` does for `dir` and `name`.
  - Safe: a NULL source to `__string()`; `__string_src()` and
    `__assign_str()` substitute `EVENT_NULL_STR`.
- **Unsafe usage**: sleeping or faulting in `TP_fast_assign()`, syscall events
  included; `trace_event_raw_event_<class>()` and `perf_trace_<class>()` hold
  `guard(preempt_notrace)()` around it.
  - Safe: per-CPU access without further protection, as `foo_timer_fn` in
    `samples/trace_events/trace-events-sample.h`.
