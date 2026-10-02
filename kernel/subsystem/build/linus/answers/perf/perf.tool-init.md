- `perf_tool__init()` in `tools/perf/util/tool.c`: assigns every member of
  `struct perf_tool`, so the tool need not be zeroed first.
- `merge_deferred_callchains`: set to `true` by `perf_tool__init()`; it is the
  one flag whose default is not zero. `dont_split_sample_group` is set to
  `false`.
- `__perf_session__new()`: reads only `ordering_requires_timestamps` and
  `ordered_events` from the tool, for its switch-off test; a write to either
  after session creation is not seen by that test.
- Callbacks: read at dispatch time, so a handler may be installed after
  session creation and before `perf_session__process_events()`, as
  `__cmd_script()` does.
- `perf_session__new()` with a NULL tool: accepted;
  `perf_session__process_event()` dereferences `session->tool`, so such a
  session cannot process events.
- `delegate_tool__init()`: copies the flags from the delegate once and sets
  every callback to a forwarder; flags changed on the delegate afterwards are
  not seen. `aslr_tool__init()` then overrides on the wrapper.
- **Unsafe usage**: processing events through a tool that never went through
  `perf_tool__init()` or `delegate_tool__init()`.
  - Unsafe: any callback left NULL; `machines__deliver_event()` and
    `perf_session__process_user_event()` call through the member with no
    NULL test.
  - Safe: `perf_tool__init()` first, then assign handlers, as `cmd_report()`
    in `tools/perf/builtin-report.c` does.
  - Safe: a tool used only as the argument of a `perf_event__handler_t`
    during synthesis, with a session created with a NULL tool, as
    `__cmd_top()` in `tools/perf/builtin-top.c` does; nothing dispatches
    through its members.
- **Potentially unsafe usage**: writing `tool->ordered_events = true` after
  `perf_tool__init(tool, false)`.
  - Unsafe: when `finished_round` is left alone; it is still
    `process_finished_round_stub()`, so no round flush happens and the queue
    holds every record until the final flush.
  - Safe: when `finished_round` is also assigned a handler that calls
    `perf_event__process_finished_round()`, as `host__finished_round()` in
    `tools/perf/builtin-inject.c` does.
  - Safe: when the init call already passed `true`, as `trace__replay()` in
    `tools/perf/builtin-trace.c` does.
