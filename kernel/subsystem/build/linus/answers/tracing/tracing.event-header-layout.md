- `TRACE_SYSTEM`: becomes `.system` of `struct trace_event_class` through
  `TRACE_SYSTEM_STRING` (`include/trace/stages/init.h`); `struct
  trace_event_call` has no system member.
- `TRACE_SYSTEM`: `include/trace/define_trace.h` never undefines it; a header
  does `#undef TRACE_SYSTEM` itself before its `#define`, outside the guard in
  `include/trace/events/sched.h`, inside it in for example
  `arch/x86/kvm/trace.h`.
- `TRACE_INCLUDE_PATH` set: the re-include is a quoted include built by
  `__stringify(TRACE_INCLUDE_PATH/system.h)`, so it is looked up first relative
  to `include/trace/` (where the including files live) and then on the `-I`
  path; `.` works only through `-I$(src)`.
- `TRACE_INCLUDE_PATH` and `TRACE_INCLUDE_FILE`: macro-expanded before being
  stringified, so a path component that is also a macro name is replaced.
- `TRACE_INCLUDE_PATH` / `TRACE_INCLUDE_FILE` defined by a header: stay defined
  after `define_trace.h` (it undefines only its own defaults, see
  `UNDEF_TRACE_INCLUDE_PATH`); a later trace header in the same `.c` inherits
  them unless it does `#undef` first.
- Guard without `|| defined(TRACE_HEADER_MULTI_READ)`: every re-read is empty,
  including the first one in `define_trace.h` that expands `DEFINE_TRACE()`,
  so neither the tracepoint nor the event is defined.
- `CREATE_TRACE_POINTS` in two files linked together: the clash is on the
  non-static objects from `__DEFINE_TRACE_EXT()` in
  `include/linux/tracepoint.h` (`__tracepoint_<name>`, `__traceiter_<name>`,
  `__probestub_<name>`, the static call); the event structures and strings are
  `static` and do not clash.
