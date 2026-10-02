- `dyn_event_release()`: does not call `is_busy`; it calls `match`, then
  `free`, and learns that an event is in use only from the error `free`
  returns.
- `dyn_event_release()` and `dyn_events_release_all()`: take `event_mutex`
  themselves; a caller that holds it deadlocks.
- `is_busy` and `free` test different things: for example
  `trace_kprobe_is_busy()` tests only `trace_probe_is_enabled()`, while
  `unregister_trace_kprobe()` also tests `trace_event_dyn_busy()`.
- Third busy test inside `free`: `trace_remove_event_call()` returns -EBUSY
  for a non-zero `perf_refcount` (under `CONFIG_PERF_EVENTS`) or a file with
  `EVENT_FILE_FL_ENABLED`; see `probe_remove_event_call()` in
  `kernel/trace/trace_events.c`.
- `dyn_events_release_all()`: the `is_busy` pass frees nothing on -EBUSY, but
  the `free` pass stops at the first error of any kind, with earlier events
  already freed.
- Sibling probes: when `trace_probe_has_sibling()` is true the probe kinds
  skip every busy test and remove that one probe, even if the event is
  enabled.
- `refcnt` in `struct trace_event_call`: opening a tracefs file does not
  raise it; the takers are the callers of `trace_event_try_get_ref()`, for
  example `perf_trace_init()` and `trace_get_event_file()`.
- `dyn_event_add()`: sets `TRACE_EVENT_FL_DYNAMIC` on the call, which is what
  makes `trace_event_try_get_ref()` use `refcnt` and not `module`.
- `create`: the framework calls it under `dyn_event_ops_mutex`, not
  `event_mutex`. A probe kind's own control file gets that lock through
  `dyn_event_create()`, as `create_or_delete_trace_kprobe()` and
  `create_or_delete_trace_uprobe()` do, because the probe log asserts it.
- `create_or_delete_synth_event()`: calls `__create_synth_event()` directly,
  without `dyn_event_ops_mutex`; synthetic events do not use the probe log.
