- `EVENT_FILE_FL_TRIGGER_COND` decides the whole order, per file.
  `update_cond_flag()` in `kernel/trace/trace_events_trigger.c` sets it when
  any trigger on the file has a filter, `EVENT_CMD_FL_POST_TRIGGER` or
  `EVENT_CMD_FL_NEEDS_REC`.

| `EVENT_FILE_FL_TRIGGER_COND` | `trace_trigger_soft_disabled()` | `trace_event_buffer_reserve()` | `__event_trigger_test_discard()` |
|---|---|---|---|
| clear | every unpaused trigger, NULL record; then soft disable; then PID filter | PID filter again | soft disable, event filter, PID filter; no triggers |
| set | returns false, nothing runs | PID filter | triggers with the record, each after its own filter, post triggers only marked; then soft disable, event filter, PID filter |

- Soft-disabled file with `EVENT_FILE_FL_TRIGGER_COND` set: the record is
  still reserved and filled, triggers see it, then it is discarded.
- PID-filtered task: triggers still fire when `EVENT_FILE_FL_TRIGGER_COND` is
  clear, and never fire when it is set, because reserve returns NULL first.
- Triggers run before the event filter and see records it will reject.
- Post triggers: `struct event_command` has no `post_trigger` member; the
  flag is `EVENT_CMD_FL_POST_TRIGGER` in `flags` of `struct event_command`,
  set only by `trigger_traceoff_cmd` and `trigger_stacktrace_cmd`.
- `event_triggers_post_call()`: runs after the commit or the discard; picks
  triggers by `trigger_type` bit, so one deferred `ETT_TRACE_ONOFF` selects
  every trigger of that type; it passes NULL for buffer, record and event.
- Per-CPU page `trace_buffered_event`: chosen in
  `trace_event_buffer_lock_reserve()` when the file has
  `EVENT_FILE_FL_SOFT_DISABLED` or `EVENT_FILE_FL_FILTERED`,
  `tr->no_filter_buffering_ref` is zero, the page is allocated,
  `trace_buffered_event_cnt` becomes 1 and `len` fits.
- `EVENT_FILE_FL_TRIGGER_COND` and `EVENT_FILE_FL_PID_FILTER` alone do not
  select the per-CPU page.
- `tr->no_filter_buffering_ref`: raised by hist triggers that use timestamps
  (`tracing_set_filter_buffering()` in `kernel/trace/trace_events_hist.c`).
- `tracing_event_time_stamp()`: for a record in the per-CPU page it returns
  the current buffer time, not a reserve time.
- `temp_buffer` in `kernel/trace/trace.c`: a second fallback, a private ring
  buffer used when the real reserve fails and `EVENT_FILE_FL_TRIGGER_COND` is
  set; `fbuffer->buffer` then points at it and the commit lands there.
- There is no event_trigger_unlock_commit_regs() here;
  `trace_event_buffer_commit()` calls `__event_trigger_test_discard()` in
  `kernel/trace/trace.h` itself.
- There is no call_filter_check_discard() here; records a tracer writes
  itself, for example `trace_function()`, are committed with
  `__buffer_unlock_commit()` and no filter test.
- **Unsafe usage**: returning after a successful
  `trace_event_buffer_reserve()` without commit or discard.
  - Safe: end with `trace_event_buffer_commit()`, or with
    `__trace_event_discard_commit()` as `user_event_ftrace()` does; both
    release the preempt count and `trace_buffered_event_cnt` that reserve
    took.
