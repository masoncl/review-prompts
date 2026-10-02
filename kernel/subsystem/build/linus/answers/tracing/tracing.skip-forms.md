- `TP_CONDITION()` under `CONFIG_LOCKDEP`: `trace_<name>()` evaluates it on
  every call, enabled or not, for the `rcu_is_watching()` warning; when
  enabled it is evaluated twice.
- `TP_CONDITION()` must therefore be free of side effects and safe to evaluate
  with the event disabled.
- Every tracepoint's condition, except the syscall variants
  (`__DECLARE_TRACE_SYSCALL()` takes none), also includes
  `cpu_online(raw_smp_processor_id())`; see `DECLARE_TRACE_EVENT()` in
  `include/linux/tracepoint.h`. A call on an offline CPU runs no probe.
- Condition examples: `smbus_write` in `include/trace/events/smbus.h` and
  `foo_bar_with_cond` in `samples/trace_events/trace-events-sample.h`;
  `include/trace/events/sched.h` has no `TRACE_EVENT_CONDITION()`, only the
  bare tracepoint `sched_set_state` from `DECLARE_TRACE_CONDITION()`, which
  like `DECLARE_TRACE()` adds `_tp` to every generated name
  (`trace_<name>_tp()`, `trace_<name>_tp_enabled()`).
- `trace_call__<name>()` inside an enabled test: fires without testing the
  key again, as `trace_call__csd_queue_cpu()` after
  `trace_csd_queue_cpu_enabled()` in `__smp_call_single_queue()`
  (`kernel/smp.c`).
- `trace_<name>()` inside an enabled test: also correct, it tests the key a
  second time.
- `trace_<name>_enabled()` under `CONFIG_LOCKDEP`: warns once if RCU is not
  watching; `__trace_<name>_enabled()` is the same test without the warning.
