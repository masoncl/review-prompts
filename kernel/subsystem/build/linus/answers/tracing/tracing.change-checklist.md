- Boot self-test: `event_trace_self_tests()` in `kernel/trace/trace_events.c`
  is under `CONFIG_EVENT_TRACE_STARTUP_TEST`; its per-event pass tests only
  events whose class has a `probe`, and skips system `syscalls` without
  `CONFIG_EVENT_TRACE_TEST_SYSCALLS`.
- BPF probe: named `__bpf_trace_<class>()`; there is no bpf_trace_<call>.
- Per-class BTF ids: `_TRACE_BTF_IDS_DECLARE()` in
  `include/trace/trace_events.h` lists `__bpf_trace_<class>` and
  `struct trace_event_raw_<class>` for `resolve_btfids` to resolve at link
  time, under `CONFIG_BPF_EVENTS` with `CONFIG_DEBUG_INFO_BTF`; an unresolved
  name is a warning, and an error under `CONFIG_WERROR`.
- Custom events: `TRACE_CUSTOM_EVENT()` in
  `include/trace/trace_custom_events.h` attaches a second record format to an
  existing tracepoint by name and type-checks it with
  `check_trace_callback_type_<name>()`; a prototype change breaks its build.
  In-tree user and build test: `samples/trace_events/trace_custom_sched.h`
  (`CONFIG_SAMPLE_TRACE_CUSTOM_EVENTS`).
- Tracepoint probe events: `tracepoint_user_register()` in
  `kernel/trace/trace_fprobe.c` registers `__probestub_<name>` as the probe;
  tests are for example `add_remove_tprobe.tc` and
  `add_remove_tprobe_module.tc` under
  `tools/testing/selftests/ftrace/test.d/dynevent/`.
- Sample module as test fixture: several tests in that directory load
  `trace-events-sample`, for example `btf_probe_event.tc`, which enables
  `foo_timer_fn`.
- Rust: `samples/rust/rust_print_events.c` defines `CREATE_RUST_TRACE_POINTS`,
  which makes `define_trace.h` emit `rust_do_trace_<name>()`.
- Runtime verification monitors: tests are in
  `tools/testing/selftests/verification`; there is no selftests/rv directory.
- Unused-tracepoint check: `TRACEPOINT_CHECK()` records each tracepoint that
  has a call site or export; `make UT=1` runs `scripts/tracepoint-update.c`,
  which warns about a defined tracepoint with neither.
- perf tests that read tracepoint fields: for example
  `tools/perf/tests/evsel-tp-sched.c` and
  `tools/perf/tests/openat-syscall-tp-fields.c`.
